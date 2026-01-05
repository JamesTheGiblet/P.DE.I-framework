const vscode = require('vscode');

function activate(context) {
    // 1. Register the Sidebar Webview Provider
    const sidebarProvider = new PdeiSidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("pdei.chatView", sidebarProvider)
    );

    // 2. Register "Ask Exocortex" Command
    context.subscriptions.push(
        vscode.commands.registerCommand('pdei.ask', () => {
            const editor = vscode.window.activeTextEditor;
            
            // Focus the sidebar container defined in package.json
            vscode.commands.executeCommand('workbench.view.extension.pdei-sidebar');

            if (editor) {
                const selection = editor.selection;
                const text = editor.document.getText(selection);
                if (text) {
                    // Send selected text to the sidebar
                    sidebarProvider.sendInput(text);
                }
            }
        })
    );
}

class PdeiSidebarProvider {
    constructor(extensionUri) {
        this._extensionUri = extensionUri;
    }

    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtml(webviewView.webview);
    }

    sendInput(text) {
        if (this._view) {
            this._view.webview.postMessage({ command: 'setInput', value: text });
        }
    }

    _getHtml(webview) {
        const config = vscode.workspace.getConfiguration('pdei');
        const port = config.get('port') || 8000;
        const hostname = config.get('hostname') || 'localhost';
        const apiUrl = `http://${hostname}:${port}/api/chat`;

        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {
                    --bg-color: var(--vscode-editor-background);
                    --text-color: var(--vscode-editor-foreground);
                    --input-bg: var(--vscode-input-background);
                    --input-fg: var(--vscode-input-foreground);
                    --button-bg: var(--vscode-button-background);
                    --button-fg: var(--vscode-button-foreground);
                    --border-color: var(--vscode-panel-border);
                }
                body {
                    font-family: var(--vscode-font-family);
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    margin: 0;
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    overflow: hidden;
                }
                /* Header */
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    background-color: var(--vscode-sideBar-background);
                    border-bottom: 1px solid var(--border-color);
                }
                .header-title { font-weight: 600; font-size: 0.9rem; }
                .icon-btn {
                    background: none;
                    border: none;
                    color: var(--vscode-icon-foreground);
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                }
                .icon-btn:hover { background-color: var(--vscode-toolbar-hoverBackground); }

                /* Chat Area */
                .chat-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 15px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .message {
                    max-width: 90%;
                    padding: 8px 12px;
                    border-radius: 6px;
                    line-height: 1.4;
                    font-size: 0.9rem;
                    word-wrap: break-word;
                }
                .user-message {
                    align-self: flex-end;
                    background-color: var(--button-bg);
                    color: var(--button-fg);
                }
                .ai-message {
                    align-self: flex-start;
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--border-color);
                }

                /* Input Area */
                .input-container {
                    padding: 10px;
                    border-top: 1px solid var(--border-color);
                    background-color: var(--vscode-sideBar-background);
                }
                textarea {
                    width: 100%;
                    background-color: var(--input-bg);
                    color: var(--input-fg);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 2px;
                    padding: 8px;
                    resize: none;
                    font-family: inherit;
                    box-sizing: border-box;
                }
                textarea:focus { outline: 1px solid var(--vscode-focusBorder); }
            </style>
        </head>
        <body>
            <div class="header">
                <button class="icon-btn" id="history-btn" title="History">🕒</button>
                <span class="header-title">Exocortex</span>
                <button class="icon-btn" id="new-chat" title="New Chat">✨</button>
            </div>

            <div class="chat-container" id="chat-container">
                <div class="message ai-message">Exocortex Online. Ready to assist.</div>
            </div>

            <div class="input-container">
                <textarea id="user-input" rows="2" placeholder="Ask Exocortex... (Enter to send)"></textarea>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                const chatContainer = document.getElementById('chat-container');
                const userInput = document.getElementById('user-input');

                // Auto-focus input
                userInput.focus();

                // Handle Input
                userInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

                document.getElementById('history-btn').addEventListener('click', async () => {
                    try {
                        const response = await fetch('${apiUrl.replace("/chat", "/history")}');
                        const data = await response.json();
                        chatContainer.innerHTML = '';
                        (data.history || []).forEach(msg => {
                            if (msg.role === 'system') return;
                            appendMessage(msg.role === 'user' ? 'user' : 'ai', msg.content);
                        });
                    } catch (e) {
                        appendMessage('ai', 'Error loading history: ' + e.message);
                    }
                });

                document.getElementById('new-chat').addEventListener('click', async () => {
                    chatContainer.innerHTML = '<div class="message ai-message">👀 Starting new session...</div>';
                    try {
                        await fetch('${apiUrl.replace("/chat", "/session/new")}', { method: 'POST' });
                    } catch (e) {
                        console.error(e);
                        appendMessage('ai', 'Warning: Failed to reset server context.');
                    }
                });

                window.addEventListener('message', event => {
                    const message = event.data;
                    if (message.command === 'setInput') {
                        userInput.value = message.value;
                        userInput.focus();
                    }
                });

                function appendMessage(role, text) {
                    const div = document.createElement('div');
                    div.className = 'message ' + (role === 'user' ? 'user-message' : 'ai-message');
                    div.textContent = text;
                    chatContainer.appendChild(div);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }

                async function sendMessage() {
                    const text = userInput.value.trim();
                    if (!text) return;

                    appendMessage('user', text);
                    userInput.value = '';

                    // Add flame indicator
                    const loadingDiv = document.createElement('div');
                    loadingDiv.className = 'message ai-message';
                    loadingDiv.textContent = '🔥 Exocortex is thinking...';
                    chatContainer.appendChild(loadingDiv);
                    chatContainer.scrollTop = chatContainer.scrollHeight;

                    try {
                        // Send to local Python Daemon
                        const response = await fetch('${apiUrl}', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message: text })
                        });

                        if (loadingDiv.parentNode) loadingDiv.remove();

                        if (!response.ok) throw new Error('API Error');
                        const data = await response.json();
                        
                        // Handle various response formats
                        const reply = data.response || data.message || JSON.stringify(data);
                        appendMessage('ai', reply);
                    } catch (err) {
                        if (loadingDiv.parentNode) loadingDiv.remove();
                        appendMessage('ai', 'Error connecting to Exocortex at ${apiUrl}. Is main.py running? Details: ' + err.message);
                        console.error(err);
                    }
                }
            </script>
        </body>
        </html>`;
    }
}

function deactivate() {}

module.exports = { activate, deactivate };