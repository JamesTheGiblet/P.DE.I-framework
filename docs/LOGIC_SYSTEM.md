# Logic & Validation System

The **P.DE.I Logic Engine** (`pdei_core/logic.py`) is a domain-agnostic validator that enforces rules defined in JSON configuration files. It ensures generated code adheres to safety standards, mathematical correctness, and style guides.

## 🏗️ Architecture

1. **Configuration**: Rules are loaded from `domain_configs/*.json`.
2. **Validation**: The `validate()` method checks code against active rules.
3. **Auto-Fix**: The `auto_fix()` method applies transformations to correct detected issues.

## 🔧 Forge Theory (Control Systems)

Defined in `domain_configs/forge_theory.json`, these rules enforce mathematical correctness in control loops and physics simulations.

| Rule ID | Trigger | Issue | Auto-Fix |
|---------|---------|-------|----------|
| `decay_negative_exponent` | `decay`, `cool` | `exp(t/tau)` (Positive exponent) | Converts to `exp(-t/tau)` |
| `growth_complement` | `charge`, `heat` | `exp(-t/tau)` (Decay form) | Converts to `(1 - exp(-t/tau))` |
| `step_response_sign` | `servo`, `motor` | `(1 - exp(t/tau))` | Fixes sign to `(1 - exp(-t/tau))` |
| `pid_dt_scaling` | `integral +=` | Missing `* dt` | Injects `* dt` into accumulation |

### Example Fix

**Input (Bad Physics):**

```cpp
float position = target * (1 - exp(t/tau)); // Runaway exponential
integral += error; // Frame-rate dependent
```

**Output (Auto-Fixed):**

```cpp
float position = target * (1 - exp(-t/tau)); // Converging exponential
integral += error * dt; // Time-scaled
```

## 🤖 Embedded Systems Rules

Defined in `domain_configs/embedded.json`, these rules ensure hardware safety and platform compatibility.

| Rule ID | Platform | Trigger | Auto-Fix |
|---------|----------|---------|----------|
| `safety_timeout` | All | `motor`, `servo` | Injects `millis() - lastCommand` failsafe |
| `esp32_pwm` | ESP32 | `analogWrite` | Replaces with `ledcWrite` |
| `esp32_adc` | ESP32 | `1023` | Scales to `4095` (12-bit resolution) |

### Safety Injection Example

If the AI generates motor code without a timeout, the system injects:

```cpp
unsigned long lastCommand = 0;
const long SAFETY_TIMEOUT = 500;

void loop() {
  if (millis() - lastCommand > SAFETY_TIMEOUT) {
    // Failsafe triggered
  }
  // ... original code ...
}
```

## 🏥 Pharma & Regulatory Rules

Defined in `domain_configs/pharma.json` (if active).

| Rule ID | Trigger | Action |
|---------|---------|--------|
| `audit_trail` | `def`, `class` | Injects `@audit_log` decorator |

## 🧩 Adding New Rules

To add a new rule, edit the relevant `domain_configs/*.json` file:

```json
{
  "id": "my_new_rule",
  "severity": "error",
  "message": "Always use specific types",
  "trigger": ["var "],
  "forbidden": ["var "],
  "suggestion": "let"
}
```

If an `auto_fix` is required, implement the handler in `pdei_core/logic.py` inside `_apply_fix`.
