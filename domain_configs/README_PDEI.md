# P.DE.I Framework Documentation

**Personal Data-driven Exocortex Intelligence**

## 🚀 Getting Started

### 1. Installation

Ensure you have Python 3.8+ and [Ollama](https://ollama.ai/) installed.

```bash
# Clone the repository
git clone https://github.com/readme-hub/P.DE.I-framework.git
cd P.DE.I-framework

# Install dependencies
pip install -r requirements.txt
```

### 2. Bootstrap a New Expert

Use the setup script to create a new personality and domain configuration. This creates the JSON files in `personalities/` and `domain_configs/`.

```bash
# Example: Create a Pharma Regulatory Assistant
python setup.py init --name "Dr. Sarah" --domain "pharma"

# Example: Create an Architecture Assistant
python setup.py init --name "John Wright" --domain "architecture"
```

### 3. Run the Executive

You can run the framework using the default configuration or override it via CLI flags.

```bash
# Run with default config (buddai_config.json)
python main.py

# Run with specific personality and domain
python main.py --personality personalities/dr_sarah.json --domain domain_configs/pharma.json

# Run in Server Mode (API + Web UI)
python main.py --server --port 8000
```

---

## 📘 Domain Configuration Schema

The `domain_configs/*.json` files define the "hard skills," validation rules, and hardware profiles for a specific domain.

### Schema Structure

```json
{
  "domain": "string (e.g., 'embedded')",
  "description": "string",
  "file_types": ["list", "of", "extensions"],
  "hardware_profiles": {
    "ProfileName": {
      "key": "value",
      "forbidden_functions": ["list"]
    }
  },
  "validation_rules": {
    "category_name": [
      {
        "id": "unique_rule_id",
        "severity": "error|warning",
        "message": "User-facing error message",
        "trigger": ["list", "of", "keywords", "that", "trigger", "check"],
        "required_pattern": "string code must contain",
        "forbidden": ["list", "of", "forbidden", "strings"],
        "exception": "string that allows forbidden pattern if present",
        "auto_fix": "function_name_in_logic_py"
      }
    ]
  }
}
```

### Rule Logic

1. **Trigger**: The rule is only evaluated if one of the trigger words appears in the generated code or the user's request context.
2. **Required Pattern**: If triggered, this string (or logic) must exist in the code.
3. **Forbidden**: If triggered, these strings must NOT exist in the code.
4. **Auto Fix**: Maps to a specific handler method in `pdei_core/logic.py` to automatically correct the code before showing it to the user.

---

## 📂 Example Domains

### Embedded Systems (`embedded.json`)

- **Focus**: Arduino/ESP32 C++
- **Rules**: Non-blocking delays, PWM usage, Safety timeouts.

### Pharmaceutical (`pharma.json`)

- **Focus**: Regulatory compliance, Data Integrity.
- **Rules**: Audit trail headers, GAMP5 validation markers.

### Architecture (`architecture.json`)

- **Focus**: Sustainable design, BIM standards.
- **Rules**: LEED material checks, ADA compliance dimensions.
