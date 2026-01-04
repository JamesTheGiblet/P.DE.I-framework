const vscode = require('vscode');
const http = require('http');

function activate(context) {
    let disposable = vscode.commands.registerCommand('pdei.ask', async function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const selection = editor.selection;
        const text = editor.document.getText(selection);
        
        if (!text) {
            vscode.window.showInformationMessage('Select some code to ask the Exocortex about.');
            return;
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Asking Exocortex...",
            cancellable: false
        }, async () => {
            try {
                const response = await queryExocortex(text);
                // Open response in a new untitled document
                const doc = await vscode.workspace.openTextDocument({ content: response, language: 'markdown' });
                await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.Beside });
            } catch (err) {
                vscode.window.showErrorMessage("Exocortex Error: " + err.message);
            }
        });
    });

    context.subscriptions.push(disposable);
}

function queryExocortex(prompt) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ message: prompt, model: "balanced" });
        const req = http.request({
            hostname: 'localhost', // Or your Tailscale IP
            port: 8000,
            path: '/api/chat',
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': data.length }
        }, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(body);
                    resolve(json.response);
                } catch (e) { reject(e); }
            });
        });
        req.on('error', (e) => reject(e));
        req.write(data);
        req.end();
    });
}

exports.activate = activate;
function deactivate() {}
exports.deactivate = deactivate;