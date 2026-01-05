# P.DE.I Framework

**Personal Data-driven Exocortex Interface**

The P.DE.I Framework is a sophisticated system designed to create a personalized AI extension of yourself. By analyzing your code repositories, commit history, and communication patterns, it creates an "Exocortex" that mirrors your coding style, values, and problem-solving methodologies.

## 🧠 Core Concepts

- **Identity Mirroring**: The AI adopts your persona, defined in `personalities/`, ensuring interactions feel like an extension of your own thought process.
- **Forge Theory**: An adaptive learning mechanism that tunes the AI's responses based on acceptance rates and retention bias.
- **Secure Context**: Built with security in mind, utilizing SSH/GPG for operations and local execution.

## 📂 Project Structure

- **`pdei_core/`**: Contains the core logic and the `learning_manifest.json` which directs the AI to your source code for training.
- **`personalities/`**:
  - `users/`: User-specific profiles (e.g., `james_the_giblet.json`).
  - `instances/`: AI personality instances (e.g., `exocortex_universal.json`).
- **`integrations/`**: Client interfaces.
  - `vscode-pdei/`: The Visual Studio Code extension to bring the Exocortex into your editor.
- **`scripts/`**: Utilities for initialization and model management.

## 🚀 Getting Started

### 1. Start the Daemon

The core of the system runs as a local daemon.
Double-click `start_daemon.bat` or run:

```cmd
start_daemon.bat
```

This will:

- Launch the P.DE.I Daemon.
- Open the Web Interface at `http://localhost:8000`.
- Initialize the Exocortex with the default personality.

### 2. VS Code Integration

To connect your editor to the Exocortex:

1. Open the `integrations/vscode-pdei` folder.
2. Install dependencies (`npm install`).
3. Run the extension.
4. Use **Ctrl+Shift+Q** to query the Exocortex.

## ⚙️ Configuration

### Learning Manifest

Edit `pdei_core/learning_manifest.json` to add your own repositories. The system uses these to learn your specific coding patterns.

### Personalities

Customize your AI's behavior by editing files in `personalities/`. You can define:

- **Core Values**: What the AI prioritizes (e.g., "IP Preservation", "Dry Humor").
- **Communication Style**: How the AI speaks.
- **Work Cycles**: Operational hours and triggers.

## 🤝 Contributing

Contributions are welcome. Please ensure any new modules adhere to the `pdei_core/template.json` structure.
