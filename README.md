# P.DE.I Framework

**Personal Data-driven Exocortex Intelligence**

> "The framework is generic. The intelligence is in the data. The personality makes it yours."

## 🧠 What is P.DE.I?

P.DE.I is a **domain-agnostic framework** designed to build Personal AI Exocortexes. Unlike generic coding assistants that rely solely on pre-trained data, P.DE.I is designed to:

1. **Capture Expertise**: Learn from your specific corrections and repositories.
2. **Enforce Methodologies**: Apply your specific rules (e.g., "Forge Theory", "GAMP5 Compliance").
3. **Adapt to Context**: Sync with your work cycles, energy levels, and personality.

It decouples the **Intelligence Engine** from the **Domain Configuration**, allowing the same core code to power a Robotics Engineer's assistant (like the reference "BuddAI") or a Pharmaceutical Regulatory aide.

## 📂 Repository Structure

- **`pdei_core/`**: The generic engine.
  - `buddai_executive.py`: Orchestrates personality, memory, and logic.
  - `logic.py`: Validates outputs against domain rules.
  - `memory.py`: Handles learning and pattern extraction.
  - `server.py`: FastAPI backend and WebSocket handler.
  - `frontend/`: React-based Web Dashboard.
- **`domain_configs/`**: Rulesets for specific industries.
  - `embedded.json`: Rules for ESP32/Arduino robotics (Reference Domain).
  - `pharma.json`: Rules for drug development workflows.
  - `forge_theory.json`: Mathematical validation rules for control systems.
  - `architecture.json`, `3d_printing.json`, `python_dev.json`, etc.: Additional domain packs.
- **`personalities/`**: User profiles.
  - `james_gilbert.json`: The reference personality (BuddAI).
  - `template.json`: A starting point for new users.
- **`launch.py`**: The universal startup script.

## 🚀 Getting Started

### 1. Installation

Ensure you have Python 3.8+ and Ollama installed.

```bash
# Clone the repository
git clone https://github.com/readme-hub/P.DE.I-framework.git
cd P.DE.I-framework

# Install dependencies
pip install -r requirements.txt
```

### Running the Reference Implementation (BuddAI)

BuddAI is the proof-of-concept implementation configured for **James Gilbert** in the **Embedded Systems** domain. The framework now includes a full Web UI.

```bash
# Launch the Server (API + Web Dashboard)
python launch.py
```

*(Note: Ensure Ollama is running before starting the framework)*

## 🛠️ Customization

### 1. Create Your Personality

Copy `personalities/template.json` to `personalities/your_name.json` and define your:

- **Identity**: Name, role, core values.
- **Work Cycles**: When you work best (e.g., "Deep Work" vs. "Admin").
- **Communication Style**: How you want the AI to talk to you.

### 2. Define Your Domain

Create a config in `domain_configs/` (e.g., `architecture.json`) defining:

- **Modules**: Key concepts in your field.
- **Validation Rules**: Strict rules the AI must follow (e.g., building codes, safety checks).

### 3. Launch

Create a `my_config.json` pointing to your new files:

```json
{
  "framework": "P.DE.I v1.0",
  "instance_name": "MyExocortex",
  "personality": "personalities/your_name.json",
  "domain": "domain_configs/architecture.json",
  "owner": "Your Name"
}
```

## 📄 License

MIT License. Build your own cognitive extension.

## ✅ Validation Status

**Date:** 2026-01-02 22:12:01  
**Summary:** 12 Tests | ✅ 12 Passed | ❌ 0 Failed | **100.0% Pass Rate**

See [test/validation_test_report.md](test/validation_test_report.md) for detailed results.
