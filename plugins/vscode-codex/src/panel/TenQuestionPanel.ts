import * as vscode from 'vscode';
import * as path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync } from 'fs';

const execFileAsync = promisify(execFile);

function existsSyncSafe(p: string): boolean {
  try { return existsSync(p); } catch { return false; }
}

export class TenQuestionProvider implements vscode.WebviewViewProvider {
  private view: vscode.WebviewView | undefined;
  private readonly extensionUri: vscode.Uri;

  constructor(extensionUri: vscode.Uri) {
    this.extensionUri = extensionUri;
  }

  public resolveWebviewView(view: vscode.WebviewView) {
    this.view = view;
    view.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, 'out', 'panel')],
    };
    view.webview.html = this.getHtml();
    view.webview.onDidReceiveMessage(msg => this.onMessage(msg));
  }

  public analyzePdf(pdfPath: string) {
    if (!this.view) return;
    this.view.webview.postMessage({ type: 'status', text: '正在解析PDF...' });
    this.runAnalysis(pdfPath);
  }

  private async runAnalysis(pdfPath: string) {
    if (!this.view) return;
    try {
      const python = this.getPythonPath();
      const repoRoot = this.resolveCoreRoot();
      if (!repoRoot) {
        this.view.webview.postMessage({
          type: 'error',
          text: '无法定位 Python 运行时 core/ 包。\n\n'
            + 'VSIX 单独安装后不再硬编码相对路径。请任选其一：\n'
            + '1. 在 VS Code 中打开本仓库源码目录（推荐方式见 README「Codex Skill」）；\n'
            + '2. 在设置中配置 tqpr.corePath 指向仓库根目录；\n'
            + '3. 直接使用命令行：python .codex/skills/ten-question-paper-reader/scripts/tqpr.py parse --pdf <你的PDF>',
        });
        return;
      }
      const coreDir = path.join(repoRoot, 'core');

      // Step 1: parse PDF
      const { stdout: paperJson } = await execFileAsync(python, [
        '-m', 'core.cli', 'parse', '--pdf', pdfPath,
      ], { cwd: repoRoot, maxBuffer: 10 * 1024 * 1024 });

      const paperJsonPath = path.join(repoRoot, '.tqpr-paper.json');
      await vscode.workspace.fs.writeFile(
        vscode.Uri.file(paperJsonPath), Buffer.from(paperJson, 'utf-8'),
      );

      this.view.webview.postMessage({ type: 'status', text: '正在调用LLM生成十问答案（约30秒）...' });

      // Step 2: generate
      const { stdout: noteJson } = await execFileAsync(python, [
        '-m', 'core.cli', 'generate', '--paper', paperJsonPath,
      ], { cwd: repoRoot, maxBuffer: 10 * 1024 * 1024, timeout: 180000 });

      this.view.webview.postMessage({ type: 'result', data: JSON.parse(noteJson) });
      this.view.webview.postMessage({ type: 'status', text: '✅ 解析完成' });
    } catch (err: any) {
      this.view.webview.postMessage({
        type: 'error',
        text: `分析失败：${err.message || err}\n\n排查清单：\n1. pip install -r requirements.txt\n2. 设置 OPENAI_API_KEY\n3. 在设置中配置 tqpr.pythonPath`,
      });
    }
  }

  private async onMessage(msg: { type: string; payload?: any }) {
    if (msg.type === 'select-pdf') {
      const uri = await vscode.window.showOpenDialog({
        filters: { PDF: ['pdf'] },
        openLabel: '选择论文PDF',
      });
      if (uri && uri.length > 0) this.analyzePdf(uri[0].fsPath);
    } else if (msg.type === 'evaluate') {
      // MVP: evaluation requires note JSON; we skip the full pipeline here
      // and just show a placeholder message.
      this.view?.webview.postMessage({
        type: 'evaluation',
        data: {
          score: 0,
          dimension_scores: {},
          strengths: [],
          weaknesses: ['MVP版本请在配置好API Key后通过CLI运行 evaluate 命令'],
          suggestions: ['python -m core.cli evaluate --note .tqpr-paper.json --summary @summary.txt'],
        },
      });
    } else if (msg.type === 'export-md') {
      const uri = await vscode.window.showSaveDialog({
        filters: { Markdown: ['md'] },
        saveLabel: '保存精读笔记',
      });
      if (uri) {
        await vscode.workspace.fs.writeFile(uri, Buffer.from(msg.payload.markdown, 'utf-8'));
        vscode.window.showInformationMessage('精读笔记已导出：' + uri.fsPath);
      }
    }
  }

  private getPythonPath(): string {
    return vscode.workspace.getConfiguration('tqpr').get<string>('pythonPath', 'python');
  }

  /**
   * Locate the repo root that contains the Python `core/` package.
   * Order of precedence:
   *   1. `tqpr.corePath` setting (explicit user override).
   *   2. Walk upward from this extension's install URI until a folder with
   *      `core/config.py` is found (handles running from source checkout).
   *   3. Search currently open workspace folders.
   * Returns null when nothing matches; the caller surfaces a helpful message.
   */
  private resolveCoreRoot(): string | null {
    const cfg = vscode.workspace.getConfiguration('tqpr');
    const configured = cfg.get<string>('corePath', '');
    if (configured) {
      const candidate = path.join(configured, 'core', 'config.py');
      if (existsSyncSafe(candidate)) return configured;
    }

    // Walk up from extensionUri.
    let cursor = this.extensionUri.fsPath;
    for (let i = 0; i < 8; i++) {
      if (existsSyncSafe(path.join(cursor, 'core', 'config.py'))) return cursor;
      const parent = path.dirname(cursor);
      if (parent === cursor) break;
      cursor = parent;
    }

    // Search open workspace folders.
    for (const folder of vscode.workspace.workspaceFolders ?? []) {
      if (existsSyncSafe(path.join(folder.uri.fsPath, 'core', 'config.py'))) {
        return folder.uri.fsPath;
      }
    }
    return null;
  }

  private getHtml(): string {
    const scriptUri = this.view!.webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'out', 'panel', 'main.js'));
    const styleUri = this.view!.webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'out', 'panel', 'main.css'));
    const nonce = getNonce();
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'none'; style-src ${this.view!.webview.cspSource}; script-src 'nonce-${nonce}';">
  <link rel="stylesheet" href="${styleUri}">
</head>
<body>
  <header>
    <h1>📑 十问精读器</h1>
    <button id="select-pdf">选择论文PDF</button>
  </header>
  <div id="status" class="status">上传论文PDF开始精读</div>
  <div id="content"></div>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
  }
}

function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) text += possible.charAt(Math.floor(Math.random() * possible.length));
  return text;
}
