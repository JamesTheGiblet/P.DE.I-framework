import json
import sys
import os
from pathlib import Path
from datetime import datetime
import textwrap

# Add parent directory to path to import pdei_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdei_core.logic import PDEIValidator

RESULTS = []

def log_result(category, test_name, status, details="", code_before="", code_after=""):
    icon = "✅" if status else "❌"
    print(f"{icon} [{category}] {test_name}")
    if details and not status:
        print(f"   {details}")
    
    RESULTS.append({
        "category": category,
        "name": test_name,
        "status": "PASS" if status else "FAIL",
        "details": details,
        "code_before": code_before,
        "code_after": code_after,
        "timestamp": datetime.now().strftime('%H:%M:%S')
    })

def export_results():
    report_path = Path(__file__).parent / "validation_test_report.md"
    
    # Calculate stats
    total = len(RESULTS)
    passed = len([r for r in RESULTS if r['status'] == 'PASS'])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# P.DE.I Validation Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Summary:** {total} Tests | ✅ {passed} Passed | ❌ {failed} Failed | **{pass_rate:.1f}% Pass Rate**\n\n")
        
        f.write("## Detailed Results\n\n")
        
        current_category = ""
        
        for r in RESULTS:
            if r['category'] != current_category:
                f.write(f"### {r['category']}\n\n")
                f.write("| Status | Test Case | Details |\n")
                f.write("| :---: | :--- | :--- |\n")
                current_category = r['category']
            
            status_icon = "✅" if r['status'] == "PASS" else "❌"
            # Escape pipes in details
            details = r['details'].replace("|", "\\|").replace("\n", "<br>")
            f.write(f"| {status_icon} | **{r['name']}** | {details} |\n")
            
            if r['code_before'] or r['code_after']:
                f.write(f"\n<details><summary>View Code Diff</summary>\n\n")
                if r['code_before']:
                    f.write(f"**Input:**\n```cpp\n{r['code_before'].strip()}\n```\n")
                if r['code_after']:
                    f.write(f"**Output/Fix:**\n```cpp\n{r['code_after'].strip()}\n```\n")
                f.write("</details>\n\n")

    print(f"\n📄 Detailed report exported to: {report_path}")

def test_embedded_validation():
    print("\n🧪 Testing Embedded Domain Rules...")
    
    # 1. Load Config
    project_root = Path(__file__).parent.parent
    config_path = project_root / "domain_configs/embedded.json"
    
    try:
        with open(config_path, 'r') as f:
            domain_config = json.load(f)
        log_result("Setup", "Load Domain Config", True)
    except Exception as e:
        log_result("Setup", "Load Domain Config", False, str(e))
        return

    validator = PDEIValidator(domain_config)
    log_result("Setup", "Initialize Validator", True)

    # --- Safety Rules ---
    
    # Test 1: Blocking Delay
    code_delay = """
    void loop() {
        digitalWrite(LED, HIGH);
        delay(1000); // Bad
    }
    """
    valid, issues = validator.validate(code_delay, context="Arduino")
    issue = next((i for i in issues if "delay" in i['message']), None)
    log_result("Safety", "Detect Blocking Delay", not valid and issue is not None, 
               f"Found: {issue['message'] if issue else 'None'}", code_before=code_delay)

    # Test 2: Safety Timeout (Detection)
    code_timeout = """
    void loop() {
        // Motor control without timeout
        digitalWrite(MOTOR_PIN, HIGH);
    }
    """
    valid, issues = validator.validate(code_timeout, context="motor control")
    issue = next((i for i in issues if i['id'] == 'safety_timeout'), None)
    log_result("Safety", "Detect Missing Safety Timeout", not valid and issue is not None,
               f"Found: {issue['message'] if issue else 'None'}", code_before=code_timeout)

    # --- Hardware Specific Rules ---

    # Test 3: ESP32 PWM (analogWrite forbidden)
    code_pwm = "analogWrite(PIN, 128);"
    valid, issues = validator.validate(code_pwm, context="ESP32")
    issue = next((i for i in issues if i['id'] == 'esp32_pwm'), None)
    log_result("Hardware", "Detect ESP32 analogWrite", not valid and issue is not None,
               f"Found: {issue['message'] if issue else 'None'}", code_before=code_pwm)

    # Test 4: ESP32 ADC (1023 resolution check)
    code_adc = "int val = map(x, 0, 1023, 0, 255);"
    valid, issues = validator.validate(code_adc, context="ESP32")
    issue = next((i for i in issues if i['id'] == 'esp32_adc'), None)
    log_result("Hardware", "Detect ESP32 10-bit ADC", not valid and issue is not None,
               f"Found: {issue['message'] if issue else 'None'}", code_before=code_adc)

    # Test 5: Arduino Context (Should allow analogWrite)
    valid, issues = validator.validate(code_pwm, context="Arduino")
    # Should be valid or at least not trigger esp32_pwm
    esp_issue = next((i for i in issues if i['id'] == 'esp32_pwm'), None)
    log_result("Hardware", "Allow analogWrite on Arduino", esp_issue is None,
               f"Issues found: {issues}", code_before=code_pwm)

    # --- Auto-Fixes ---

    # Test 6: Auto-Fix ESP32 PWM
    if not valid: # Re-using result from Test 3
        # We need to re-validate to get issues if we want to be clean, but we have them
        _, issues_pwm = validator.validate(code_pwm, context="ESP32")
        fixed = validator.auto_fix(code_pwm, issues_pwm)
        success = "ledcWrite(PIN, 128);" in fixed
        log_result("Auto-Fix", "Fix ESP32 PWM", success, 
                   f"Expected ledcWrite, got: {fixed}", code_before=code_pwm, code_after=fixed)

    # Test 7: Auto-Fix ESP32 ADC
    _, issues_adc = validator.validate(code_adc, context="ESP32")
    fixed_adc = validator.auto_fix(code_adc, issues_adc)
    success = "4095" in fixed_adc
    log_result("Auto-Fix", "Fix ESP32 ADC Resolution", success,
               f"Expected 4095, got: {fixed_adc}", code_before=code_adc, code_after=fixed_adc)

    # Test 8: Auto-Fix Safety Timeout Injection
    code_safety_fix_input = """
void setup() {
  pinMode(M1, OUTPUT);
}
void loop() {
  digitalWrite(M1, HIGH);
}
"""
    _, issues_safety = validator.validate(code_safety_fix_input, context="motor")
    fixed_safety = validator.auto_fix(code_safety_fix_input, issues_safety)
    success = "SAFETY_TIMEOUT" in fixed_safety and "lastCommand" in fixed_safety
    log_result("Auto-Fix", "Inject Safety Timeout", success,
               "Checked for SAFETY_TIMEOUT constant and logic", code_before=code_safety_fix_input, code_after=fixed_safety)

def test_pharma_validation():
    print("\n🧪 Testing Pharma Domain Rules (Mock)...")
    
    pharma_config = {
        "domain": "pharma",
        "validation_rules": {
            "compliance": [{
                "id": "audit_header",
                "trigger": ["def ", "class "],
                "required_pattern": "@audit_log",
                "auto_fix": "inject_audit_header",
                "severity": "error",
                "message": "Missing audit log decorator"
            }]
        }
    }
    
    pharma_validator = PDEIValidator(pharma_config)
    
    # Test 9: Detect Missing Audit Header
    code_pharma = "def calculate_dose(w): return w*2"
    valid, issues = pharma_validator.validate(code_pharma, context="pharma")
    issue = next((i for i in issues if i['id'] == 'audit_header'), None)
    log_result("Pharma", "Detect Missing Audit Header", not valid and issue is not None,
               f"Found: {issue['message'] if issue else 'None'}", code_before=code_pharma)
    
    # Test 10: Auto-Fix Audit Header
    fixed_pharma = pharma_validator.auto_fix(code_pharma, issues)
    success = "@audit_log\ndef calculate_dose" in fixed_pharma
    log_result("Pharma", "Inject Audit Header", success,
               "Checked for @audit_log decorator", code_before=code_pharma, code_after=fixed_pharma)

    # Test 11: Idempotency (Don't double inject)
    code_pharma_existing = "@audit_log\ndef existing_func(): pass"
    valid, issues = pharma_validator.validate(code_pharma_existing, context="pharma")
    # Should be valid
    log_result("Pharma", "Respect Existing Header", valid,
               f"Issues found: {issues}", code_before=code_pharma_existing)

if __name__ == "__main__":
    test_embedded_validation()
    test_pharma_validation()
    export_results()