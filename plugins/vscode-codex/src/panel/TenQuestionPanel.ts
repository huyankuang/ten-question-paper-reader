import * as vscode from 'vscode';
import * as path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

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
      // core/ is at the repo root; the extension lives at plugins/vscode-codex/
      const repoRoot = path.join(this.extensionUri.fsPath, '..', '..', '..');
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
