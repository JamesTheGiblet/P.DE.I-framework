import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import pdei_core
sys.path.append(str(Path(__file__).parent.parent))

from pdei_core.logic import PDEIValidator

def test_embedded_validation():
    print("🧪 Testing P.DE.I Generic Validator with Embedded Domain...")
    
    # 1. Load the Domain Config
    project_root = Path(__file__).parent.parent
    config_path = project_root / "domain_configs/embedded.json"
    if not config_path.exists():
        print(f"❌ Config not found at {config_path}")
        return

    with open(config_path, 'r') as f:
        domain_config = json.load(f)
    
    validator = PDEIValidator(domain_config)
    print("✅ Validator initialized with embedded rules.")

    # 2. Test Case: Blocking Delay (Should Fail)
    bad_code = """
    void loop() {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(1000); // Blocking!
    }
    """
    valid, issues = validator.validate(bad_code, context="Arduino")
    if not valid and any("delay()" in i['message'] for i in issues):
        print("✅ Correctly caught blocking delay().")
    else:
        print("❌ Failed to catch blocking delay().")

    # 3. Test Case: ESP32 AnalogWrite (Should Fail on ESP32)
    esp_code = """
    void setup() {
        analogWrite(PIN, 128);
    }
    """
    valid, issues = validator.validate(esp_code, context="ESP32")
    if not valid and any("ledcWrite" in i['message'] for i in issues):
        print("✅ Correctly caught analogWrite on ESP32.")
    else:
        print("❌ Failed to catch analogWrite on ESP32.")

    # 4. Test Case: Clean Code (Should Pass)
    good_code = "unsigned long currentMillis = millis();"
    valid, issues = validator.validate(good_code, context="ESP32")
    if valid:
        print("✅ Clean code passed validation.")
    else:
        print(f"❌ Clean code failed validation: {issues}")

if __name__ == "__main__":
    test_embedded_validation()