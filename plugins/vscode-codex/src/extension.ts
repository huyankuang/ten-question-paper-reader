import * as vscode from 'vscode';
import { TenQuestionProvider } from './panel/TenQuestionPanel';

export function activate(context: vscode.ExtensionContext) {
  const provider = new TenQuestionProvider(context.extensionUri);

  const registration = vscode.window.registerWebviewViewProvider(
    'tqpr-panel',
    provider,
    { webviewOptions: { retainContextWhenHidden: true } }
  );

  const openPanel = vscode.commands.registerCommand('tqpr.openPanel', () => {
    vscode.commands.executeCommand('workbench.view.extension.tqpr-sidebar');
  });

  const analyzePdf = vscode.commands.registerCommand('tqpr.analyzePdf', async () => {
    const activeEditor = vscode.window.activeTextEditor;
    let pdfPath: string | undefined;
    if (activeEditor && activeEditor.document.uri.fsPath.toLowerCase().endsWith('.pdf')) {
      pdfPath = activeEditor.document.uri.fsPath;
    } else {
      const uri = await vscode.window.showOpenDialog({
        filters: { 'PDF': ['pdf'] },
        openLabel: '选择要精读的论文PDF',
      });
      if (uri && uri.length > 0) pdfPath = uri[0].fsPath;
    }
    if (pdfPath) {
      await vscode.commands.executeCommand('workbench.view.extension.tqpr-sidebar');
      provider.analyzePdf(pdfPath);
    }
  });

  context.subscriptions.push(registration, openPanel, analyzePdf);
}

export function deactivate() {}
