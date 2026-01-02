import json
import sys
import os
import shutil
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
    
    overall_status = "PASSED" if failed == 0 else "FAILED"
    status_icon = "✅" if failed == 0 else "❌"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# P.DE.I Validation Test Report\n\n")
        f.write(f"# {status_icon} {overall_status}\n\n")
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

    # Archive stamped copy
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    stamped_path = reports_dir / f"validation_report_{timestamp}.md"
    shutil.copy(report_path, stamped_path)

    print(f"\n📄 Detailed report exported to: {report_path}")
    print(f"🗃️  Stamped copy archived to: {stamped_path}")

def load_validator(domain_name):
    project_root = Path(__file__).parent.parent
    config_path = project_root / f"domain_configs/{domain_name}.json"
    try:
        with open(config_path, 'r') as f:
            return PDEIValidator(json.load(f))
    except Exception as e:
        print(f"❌ Error loading {domain_name}: {e}")
        return None

def run_test_case(validator, domain, test_id, name, code, context, expected_valid, expected_issue_id=None, auto_fix_check=None):
    valid, issues = validator.validate(code, context=context)
    
    # Check Validity
    status = (valid == expected_valid)
    details = f"Expected valid={expected_valid}, got {valid}"
    
    # Check Specific Issue ID
    if expected_issue_id:
        found_issue = next((i for i in issues if i['id'] == expected_issue_id), None)
        if not found_issue:
            status = False
            details += f" | Missing expected issue: {expected_issue_id}"
        else:
            details += f" | Found issue: {found_issue['message']}"
            
            # Check Auto-Fix if requested
            if auto_fix_check and 'auto_fix' in found_issue:
                fixed_code = validator.auto_fix(code, issues)
                if not auto_fix_check(fixed_code):
                    status = False
                    details += f" | Auto-fix failed. Result: {fixed_code.strip()}"
                else:
                    details += " | Auto-fix verified"

    log_result(domain, f"#{test_id} {name}", status, details, code_before=code)

def run_100_tests():
    print("\n🚀 Running 100-Test Validation Suite...")
    
    # --- 1. Embedded Systems (10 Tests) ---
    v = load_validator("embedded")
    if v:
        run_test_case(v, "Embedded", 1, "Blocking Delay", "delay(1000);", "Arduino", False, "non_blocking")
        run_test_case(v, "Embedded", 2, "Clean Delay", "currentMillis - previousMillis", "Arduino", True)
        run_test_case(v, "Embedded", 3, "Safety Timeout", "void loop() { digitalWrite(M1, HIGH); }", "motor", False, "safety_timeout", lambda c: "SAFETY_TIMEOUT" in c)
        run_test_case(v, "Embedded", 4, "ESP32 PWM", "analogWrite(P, 100);", "ESP32", False, "esp32_pwm", lambda c: "ledcWrite" in c)
        run_test_case(v, "Embedded", 5, "ESP32 ADC", "val = 1023;", "ESP32", False, "esp32_adc", lambda c: "4095" in c)
        run_test_case(v, "Embedded", 6, "Naming Convention", "void MyFunc() {}", "Arduino", True) # Warning only
        run_test_case(v, "Embedded", 7, "Arduino PWM", "analogWrite(P, 100);", "Arduino", True)
        run_test_case(v, "Embedded", 8, "Setup Exception", "void setup() { delay(100); }", "Arduino", True)
        run_test_case(v, "Embedded", 9, "Clean Motor", "if(millis() - lastCommand > SAFETY_TIMEOUT) digitalWrite(M1, H);", "motor", True)
        run_test_case(v, "Embedded", 10, "Complex Logic", "state = IDLE;", "logic", True)

    # --- 2. Pharma (10 Tests) ---
    v = load_validator("pharma")
    if v:
        run_test_case(v, "Pharma", 11, "Missing Audit", "def process_data():", "lab", False, "audit_trail_header", lambda c: "@audit_log" in c)
        run_test_case(v, "Pharma", 12, "Existing Audit", "@audit_log\ndef process():", "lab", True)
        run_test_case(v, "Pharma", 13, "Data Integrity", "db.save(x)", "lab", True) # Warning
        run_test_case(v, "Pharma", 14, "Clean Calc", "x = y + 2", "lab", True)
        run_test_case(v, "Pharma", 15, "Class Audit", "class Experiment:", "lab", False, "audit_trail_header")
        run_test_case(v, "Pharma", 16, "Export Warning", "data.export()", "lab", True) # Warning
        run_test_case(v, "Pharma", 17, "Immutable Pattern", "data.save(immutable=True)", "lab", True)
        run_test_case(v, "Pharma", 18, "Process Trigger", "def run_process():", "lab", False, "audit_trail_header")
        run_test_case(v, "Pharma", 19, "Comment Ignore", "# def commented_out():", "lab", True)
        run_test_case(v, "Pharma", 20, "Empty File", "", "lab", True)

    # --- 3. Architecture (10 Tests) ---
    v = load_validator("architecture")
    if v:
        run_test_case(v, "Arch", 21, "ADA Violation", "door_width = 30", "plan", False, "ada_compliance", lambda c: "36" in c)
        run_test_case(v, "Arch", 22, "ADA Compliant", "if (width >= 36) door_width = 36;", "plan", True)
        run_test_case(v, "Arch", 23, "Hallway Width", "hallway = 32", "plan", False, "ada_compliance", lambda c: "36" in c)
        run_test_case(v, "Arch", 24, "LEED Warning", "material = 'concrete'", "plan", True) # Warning
        run_test_case(v, "Arch", 25, "LEED Certified", "material = 'LEED_Certified concrete'", "plan", True)
        run_test_case(v, "Arch", 26, "Ramp Width", "ramp_width = 24", "plan", False, "ada_compliance")
        run_test_case(v, "Arch", 27, "Window (No Rule)", "window_width = 20", "plan", True)
        run_test_case(v, "Arch", 28, "Steel Material", "structure = 'steel'", "plan", True) # Warning
        run_test_case(v, "Arch", 29, "Wood Material", "frame = 'wood'", "plan", True) # Warning
        run_test_case(v, "Arch", 30, "Corridor Fix", "corridor = 10", "plan", False, "ada_compliance", lambda c: "36" in c)

    # --- 4. 3D Printing (10 Tests) ---
    v = load_validator("3d_printing")
    if v:
        run_test_case(v, "3DPrint", 31, "Heater Safety", "M104 S200", "gcode", True)
        run_test_case(v, "3DPrint", 32, "Unsafe Heater", "M104", "gcode", False, "thermal_runaway")
        run_test_case(v, "3DPrint", 33, "Bed Adhesion", "start_gcode", "gcode", True) # Warning
        run_test_case(v, "3DPrint", 34, "Bed Adhesion OK", "start_gcode\nM140 S60", "gcode", True)
        run_test_case(v, "3DPrint", 35, "Fan Speed OK", "M106 S255", "gcode", True)
        run_test_case(v, "3DPrint", 36, "Fan Speed High", "M106 S300", "gcode", False, "fan_speed_limit")
        run_test_case(v, "3DPrint", 37, "Fan Speed Bad", "M106 S999", "gcode", False, "fan_speed_limit")
        run_test_case(v, "3DPrint", 38, "Wait Temp", "M109 S210", "gcode", True)
        run_test_case(v, "3DPrint", 39, "Move Command", "G1 X10 Y10", "gcode", True)
        run_test_case(v, "3DPrint", 40, "Home Command", "G28", "gcode", True)

    # --- 5. Python Dev (10 Tests) ---
    v = load_validator("python_dev")
    if v:
        run_test_case(v, "Python", 41, "Missing Types", "def func(a):", "dev", True) # Warning
        run_test_case(v, "Python", 42, "With Types", "def func(a: int):", "dev", True)
        run_test_case(v, "Python", 43, "Print in Prod", "print('debug')", "dev", True) # Warning
        run_test_case(v, "Python", 44, "Print in Main", "if __name__ == \"__main__\":\n print('ok')", "dev", True)
        run_test_case(v, "Python", 45, "Missing Docstring", "def my_api():", "dev", True) # Warning
        run_test_case(v, "Python", 46, "With Docstring", "def api():\n \"\"\"Doc\"\"\"", "dev", True)
        run_test_case(v, "Python", 47, "Class Def", "class MyClass:", "dev", True)
        run_test_case(v, "Python", 48, "Import", "import os", "dev", True)
        run_test_case(v, "Python", 49, "Variable", "x = 1", "dev", True)
        run_test_case(v, "Python", 50, "Lambda", "lambda x: x", "dev", True)

    # --- 6. Web Dev (10 Tests) ---
    v = load_validator("web_dev")
    if v:
        run_test_case(v, "Web", 51, "Missing Alt", "<img src='x.jpg'>", "html", False, "img_alt")
        run_test_case(v, "Web", 52, "With Alt", "<img src='x' alt='desc'>", "html", True)
        run_test_case(v, "Web", 53, "Button Type", "<button>Click</button>", "html", True) # Warning
        run_test_case(v, "Web", 54, "Button Type OK", "<button type='button'>", "html", True)
        run_test_case(v, "Web", 55, "Hook in Loop", "for(i=0;i<5;i++) { useEffect() }", "react", False, "hooks_rules")
        run_test_case(v, "Web", 56, "Hook in Cond", "if(x) { useState() }", "react", False, "hooks_rules")
        run_test_case(v, "Web", 57, "Valid Hook", "useEffect(() => {})", "react", True)
        run_test_case(v, "Web", 58, "Div Tag", "<div></div>", "html", True)
        run_test_case(v, "Web", 59, "Span Tag", "<span></span>", "html", True)
        run_test_case(v, "Web", 60, "Input Tag", "<input />", "html", True)

    # --- 7. Data Science (10 Tests) ---
    v = load_validator("data_science")
    if v:
        run_test_case(v, "DataSci", 61, "No Seed", "RandomForest()", "ml", True) # Warning
        run_test_case(v, "DataSci", 62, "With Seed", "RandomForest(random_state=42)", "ml", True)
        run_test_case(v, "DataSci", 63, "Hardcoded Path", "pd.read_csv('C:/Users/data.csv')", "ml", False, "no_hardcoded_paths")
        run_test_case(v, "DataSci", 64, "Relative Path", "pd.read_csv('data.csv')", "ml", True)
        run_test_case(v, "DataSci", 65, "OS Path", "open(os.path.join(d, 'f'))", "ml", True)
        run_test_case(v, "DataSci", 66, "Split No Seed", "train_test_split(X, y)", "ml", True) # Warning
        run_test_case(v, "DataSci", 67, "Split Seed", "train_test_split(random_state=1)", "ml", True)
        run_test_case(v, "DataSci", 68, "Linux Path", "open('/home/user/file')", "ml", False, "no_hardcoded_paths")
        run_test_case(v, "DataSci", 69, "Sample No Seed", "df.sample(n=5)", "ml", True) # Warning
        run_test_case(v, "DataSci", 70, "Clean Code", "import pandas as pd", "ml", True)

    # --- 8. Cybersecurity (10 Tests) ---
    v = load_validator("cybersecurity")
    if v:
        run_test_case(v, "Cyber", 71, "SQL Injection", "q = f\"SELECT * FROM users WHERE id={id}\"", "backend", False, "sql_injection")
        run_test_case(v, "Cyber", 72, "Safe SQL", "cursor.execute('SELECT ?', (id,))", "backend", True)
        run_test_case(v, "Cyber", 73, "Hardcoded Key", "api_key = \"sk-12345\"", "backend", False, "hardcoded_secrets")
        run_test_case(v, "Cyber", 74, "Env Var Key", "api_key = os.getenv('KEY')", "backend", True)
        run_test_case(v, "Cyber", 75, "Hardcoded Pass", "password = \"123456\"", "backend", False, "hardcoded_secrets")
        run_test_case(v, "Cyber", 76, "Format SQL", "sql = \"INSERT {}\".format(val)", "backend", False, "sql_injection")
        run_test_case(v, "Cyber", 77, "Concat SQL", "sql = \"UPDATE \" + val", "backend", False, "sql_injection")
        run_test_case(v, "Cyber", 78, "Safe Var", "user_id = 5", "backend", True)
        run_test_case(v, "Cyber", 79, "Config Var", "timeout = 500", "backend", True)
        run_test_case(v, "Cyber", 80, "Secret in Name", "my_secret_func()", "backend", True) # Trigger word but no forbidden pattern

    # --- 9. Game Dev (10 Tests) ---
    v = load_validator("game_dev")
    if v:
        run_test_case(v, "GameDev", 81, "No DeltaTime", "transform.Translate(Vector3.up)", "unity", False, "delta_time")
        run_test_case(v, "GameDev", 82, "With DeltaTime", "transform.Translate(Vector3.up * Time.deltaTime)", "unity", True)
        run_test_case(v, "GameDev", 83, "Find in Update", "void Update() { GameObject.Find('Player'); }", "unity", False, "find_in_update") # Warning
        run_test_case(v, "GameDev", 84, "Find in Start", "void Start() { GameObject.Find('Player'); }", "unity", True)
        run_test_case(v, "GameDev", 85, "GetComponent Update", "void Update() { GetComponent<Rb>(); }", "unity", False, "find_in_update") # Warning
        run_test_case(v, "GameDev", 86, "Vector Math", "Vector3 pos = new Vector3(0,0,0);", "unity", True)
        run_test_case(v, "GameDev", 87, "FixedUpdate", "void FixedUpdate() {}", "unity", True)
        run_test_case(v, "GameDev", 88, "OnCollision", "void OnCollisionEnter() {}", "unity", True)
        run_test_case(v, "GameDev", 89, "Debug Log", "Debug.Log('hit')", "unity", True)
        run_test_case(v, "GameDev", 90, "Instantiate", "Instantiate(prefab)", "unity", True)

    # --- 10. Mobile Dev (10 Tests) ---
    v = load_validator("mobile_dev")
    if v:
        run_test_case(v, "Mobile", 91, "Block Main", "URL(url).readText()", "android", False, "main_thread_blocking")
        run_test_case(v, "Mobile", 92, "Async Net", "async { URL(url).readText() }", "android", True)
        run_test_case(v, "Mobile", 93, "Camera Perm", "Camera.open()", "android", True) # Warning
        run_test_case(v, "Mobile", 94, "Check Perm", "if(checkPermission) Camera.open()", "android", True)
        run_test_case(v, "Mobile", 95, "HTTP Conn", "HttpURLConnection(url)", "android", False, "main_thread_blocking")
        run_test_case(v, "Mobile", 96, "Location", "LocationManager.get()", "android", True) # Warning
        run_test_case(v, "Mobile", 97, "Contacts", "ContactsContract.get()", "android", True) # Warning
        run_test_case(v, "Mobile", 98, "UI Update", "textView.setText('hi')", "android", True)
        run_test_case(v, "Mobile", 99, "Toast", "Toast.makeText()", "android", True)
        run_test_case(v, "Mobile", 100, "Log", "Log.d('tag', 'msg')", "android", True)

if __name__ == "__main__":
    run_100_tests()
    export_results()