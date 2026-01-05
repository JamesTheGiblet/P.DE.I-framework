# P.DE.I Exocortex for VS Code

**Connect your editor to your Personal Data-driven Exocortex.**

This extension integrates the P.DE.I Framework directly into Visual Studio Code, allowing you to query your personalized AI model using your current code selection as context.

## ✨ Features

- **Contextual Querying**: Select any code snippet and ask your Exocortex for analysis, refactoring, or explanation.
- **Identity Mirroring**: Responses are generated using your specific coding style and personality profile (configured in the P.DE.I core).
- **Seamless Integration**: Results appear in a new editor pane beside your code.

## 🚀 Usage

1. **Ensure the Daemon is Running**:
   The extension requires the P.DE.I local daemon to be active. Run `start_daemon.bat` from the framework root.

2. **Select Code**:
   Highlight a block of code or text in your active editor.

3. **Ask Exocortex**:
   - Press `Ctrl+Shift+Q` (or `Cmd+Shift+Q` on macOS).
   - Or run the command `Ask Exocortex` from the Command Palette (`Ctrl+Shift+P`).

4. **View Response**:
   The AI's response will open in a new Markdown document to the side.

## ⚙️ Configuration

You can configure the connection to the P.DE.I daemon in VS Code Settings (`Ctrl+,`):

| Setting | Default | Description |
| :--- | :--- | :--- |
| `pdei.hostname` | `localhost` | The hostname or IP where the P.DE.I daemon is running. |
| `pdei.port` | `8000` | The port number for the API. |

## 🔧 Requirements

- **P.DE.I Framework**: You must have the core framework installed and the daemon running locally.

---
*Part of the P.DE.I Framework by JamesTheGiblet.*
