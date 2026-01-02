# P.DE.I Validation Test Report

# ✅ PASSED

**Date:** 2026-01-02 23:00:15
**Summary:** 100 Tests | ✅ 100 Passed | ❌ 0 Failed | **100.0% Pass Rate**

## Detailed Results

### Embedded

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#1 Blocking Delay** | Expected valid=False, got False \| Found issue: Blocking delay() detected. Prefer non-blocking logic. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
delay(1000);
```
</details>

| ✅ | **#2 Clean Delay** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
currentMillis - previousMillis
```
</details>

| ✅ | **#3 Safety Timeout** | Expected valid=False, got False \| Found issue: Critical: No safety timeout detected (must be > 500ms). \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void loop() { digitalWrite(M1, HIGH); }
```
</details>

| ✅ | **#4 ESP32 PWM** | Expected valid=False, got False \| Found issue: ESP32 does not support analogWrite. Use ledcWrite instead. \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
analogWrite(P, 100);
```
</details>

| ✅ | **#5 ESP32 ADC** | Expected valid=False, got False \| Found issue: ESP32 ADC resolution is 12-bit (4095), not 10-bit (1023/1024). \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
val = 1023;
```
</details>

| ✅ | **#6 Naming Convention** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void MyFunc() {}
```
</details>

| ✅ | **#7 Arduino PWM** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
analogWrite(P, 100);
```
</details>

| ✅ | **#8 Setup Exception** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void setup() { delay(100); }
```
</details>

| ✅ | **#9 Clean Motor** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
if(millis() - lastCommand > SAFETY_TIMEOUT) digitalWrite(M1, H);
```
</details>

| ✅ | **#10 Complex Logic** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
state = IDLE;
```
</details>

### Pharma

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#11 Missing Audit** | Expected valid=False, got False \| Found issue: Critical: Missing Audit Trail Header for GxP compliance. \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def process_data():
```
</details>

| ✅ | **#12 Existing Audit** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
@audit_log
def process():
```
</details>

| ✅ | **#13 Data Integrity** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
db.save(x)
```
</details>

| ✅ | **#14 Clean Calc** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
x = y + 2
```
</details>

| ✅ | **#15 Class Audit** | Expected valid=False, got False \| Found issue: Critical: Missing Audit Trail Header for GxP compliance. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
class Experiment:
```
</details>

| ✅ | **#16 Export Warning** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
data.export()
```
</details>

| ✅ | **#17 Immutable Pattern** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
data.save(immutable=True)
```
</details>

| ✅ | **#18 Process Trigger** | Expected valid=False, got False \| Found issue: Critical: Missing Audit Trail Header for GxP compliance. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def run_process():
```
</details>

| ✅ | **#19 Comment Ignore** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
# def commented_out():
```
</details>

| ✅ | **#20 Empty File** | Expected valid=True, got True |
### Arch

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#21 ADA Violation** | Expected valid=False, got False \| Found issue: Ensure ADA compliance for accessibility (min width 36 inches). \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
door_width = 30
```
</details>

| ✅ | **#22 ADA Compliant** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
if (width >= 36) door_width = 36;
```
</details>

| ✅ | **#23 Hallway Width** | Expected valid=False, got False \| Found issue: Ensure ADA compliance for accessibility (min width 36 inches). \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
hallway = 32
```
</details>

| ✅ | **#24 LEED Warning** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
material = 'concrete'
```
</details>

| ✅ | **#25 LEED Certified** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
material = 'LEED_Certified concrete'
```
</details>

| ✅ | **#26 Ramp Width** | Expected valid=False, got False \| Found issue: Ensure ADA compliance for accessibility (min width 36 inches). |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
ramp_width = 24
```
</details>

| ✅ | **#27 Window (No Rule)** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
window_width = 20
```
</details>

| ✅ | **#28 Steel Material** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
structure = 'steel'
```
</details>

| ✅ | **#29 Wood Material** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
frame = 'wood'
```
</details>

| ✅ | **#30 Corridor Fix** | Expected valid=False, got False \| Found issue: Ensure ADA compliance for accessibility (min width 36 inches). \| Auto-fix verified |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
corridor = 10
```
</details>

### 3DPrint

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#31 Heater Safety** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
M104 S200
```
</details>

| ✅ | **#32 Unsafe Heater** | Expected valid=False, got False \| Found issue: Heater timeout safety check required. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
M104
```
</details>

| ✅ | **#33 Bed Adhesion** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
start_gcode
```
</details>

| ✅ | **#34 Bed Adhesion OK** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
start_gcode
M140 S60
```
</details>

| ✅ | **#35 Fan Speed OK** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
M106 S255
```
</details>

| ✅ | **#36 Fan Speed High** | Expected valid=False, got False \| Found issue: Fan speed M106 should not exceed 255. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
M106 S300
```
</details>

| ✅ | **#37 Fan Speed Bad** | Expected valid=False, got False \| Found issue: Fan speed M106 should not exceed 255. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
M106 S999
```
</details>

| ✅ | **#38 Wait Temp** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
M109 S210
```
</details>

| ✅ | **#39 Move Command** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
G1 X10 Y10
```
</details>

| ✅ | **#40 Home Command** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
G28
```
</details>

### Python

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#41 Missing Types** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def func(a):
```
</details>

| ✅ | **#42 With Types** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def func(a: int):
```
</details>

| ✅ | **#43 Print in Prod** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
print('debug')
```
</details>

| ✅ | **#44 Print in Main** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
if __name__ == "__main__":
 print('ok')
```
</details>

| ✅ | **#45 Missing Docstring** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def my_api():
```
</details>

| ✅ | **#46 With Docstring** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def api():
 """Doc"""
```
</details>

| ✅ | **#47 Class Def** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
class MyClass:
```
</details>

| ✅ | **#48 Import** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
import os
```
</details>

| ✅ | **#49 Variable** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
x = 1
```
</details>

| ✅ | **#50 Lambda** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
lambda x: x
```
</details>

### Web

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#51 Missing Alt** | Expected valid=False, got False \| Found issue: Images must have alt text for accessibility. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<img src='x.jpg'>
```
</details>

| ✅ | **#52 With Alt** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<img src='x' alt='desc'>
```
</details>

| ✅ | **#53 Button Type** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<button>Click</button>
```
</details>

| ✅ | **#54 Button Type OK** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<button type='button'>
```
</details>

| ✅ | **#55 Hook in Loop** | Expected valid=False, got False \| Found issue: Hooks must be called at the top level. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
for(i=0;i<5;i++) { useEffect() }
```
</details>

| ✅ | **#56 Hook in Cond** | Expected valid=False, got False \| Found issue: Hooks must be called at the top level. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
if(x) { useState() }
```
</details>

| ✅ | **#57 Valid Hook** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
useEffect(() => {})
```
</details>

| ✅ | **#58 Div Tag** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<div></div>
```
</details>

| ✅ | **#59 Span Tag** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<span></span>
```
</details>

| ✅ | **#60 Input Tag** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
<input />
```
</details>

### DataSci

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#61 No Seed** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
RandomForest()
```
</details>

| ✅ | **#62 With Seed** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
RandomForest(random_state=42)
```
</details>

| ✅ | **#63 Hardcoded Path** | Expected valid=False, got False \| Found issue: Do not use hardcoded absolute paths. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
pd.read_csv('C:/Users/data.csv')
```
</details>

| ✅ | **#64 Relative Path** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
pd.read_csv('data.csv')
```
</details>

| ✅ | **#65 OS Path** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
open(os.path.join(d, 'f'))
```
</details>

| ✅ | **#66 Split No Seed** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
train_test_split(X, y)
```
</details>

| ✅ | **#67 Split Seed** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
train_test_split(random_state=1)
```
</details>

| ✅ | **#68 Linux Path** | Expected valid=False, got False \| Found issue: Do not use hardcoded absolute paths. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
open('/home/user/file')
```
</details>

| ✅ | **#69 Sample No Seed** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
df.sample(n=5)
```
</details>

| ✅ | **#70 Clean Code** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
import pandas as pd
```
</details>

### Cyber

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#71 SQL Injection** | Expected valid=False, got False \| Found issue: Potential SQL Injection detected. Use parameterized queries. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
q = f"SELECT * FROM users WHERE id={id}"
```
</details>

| ✅ | **#72 Safe SQL** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
cursor.execute('SELECT ?', (id,))
```
</details>

| ✅ | **#73 Hardcoded Key** | Expected valid=False, got False \| Found issue: Do not hardcode API keys or passwords. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
api_key = "sk-12345"
```
</details>

| ✅ | **#74 Env Var Key** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
api_key = os.getenv('KEY')
```
</details>

| ✅ | **#75 Hardcoded Pass** | Expected valid=False, got False \| Found issue: Do not hardcode API keys or passwords. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
password = "123456"
```
</details>

| ✅ | **#76 Format SQL** | Expected valid=False, got False \| Found issue: Potential SQL Injection detected. Use parameterized queries. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
sql = "INSERT {}".format(val)
```
</details>

| ✅ | **#77 Concat SQL** | Expected valid=False, got False \| Found issue: Potential SQL Injection detected. Use parameterized queries. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
sql = "UPDATE " + val
```
</details>

| ✅ | **#78 Safe Var** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
user_id = 5
```
</details>

| ✅ | **#79 Config Var** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
timeout = 500
```
</details>

| ✅ | **#80 Secret in Name** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
my_secret_func()
```
</details>

### GameDev

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#81 No DeltaTime** | Expected valid=False, got False \| Found issue: Movement must use Time.deltaTime for frame-rate independence. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
transform.Translate(Vector3.up)
```
</details>

| ✅ | **#82 With DeltaTime** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
transform.Translate(Vector3.up * Time.deltaTime)
```
</details>

| ✅ | **#83 Find in Update** | Expected valid=False, got False \| Found issue: Avoid GameObject.Find() in Update loops. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void Update() { GameObject.Find('Player'); }
```
</details>

| ✅ | **#84 Find in Start** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void Start() { GameObject.Find('Player'); }
```
</details>

| ✅ | **#85 GetComponent Update** | Expected valid=False, got False \| Found issue: Avoid GameObject.Find() in Update loops. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void Update() { GetComponent<Rb>(); }
```
</details>

| ✅ | **#86 Vector Math** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
Vector3 pos = new Vector3(0,0,0);
```
</details>

| ✅ | **#87 FixedUpdate** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void FixedUpdate() {}
```
</details>

| ✅ | **#88 OnCollision** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void OnCollisionEnter() {}
```
</details>

| ✅ | **#89 Debug Log** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
Debug.Log('hit')
```
</details>

| ✅ | **#90 Instantiate** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
Instantiate(prefab)
```
</details>

### Mobile

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **#91 Block Main** | Expected valid=False, got False \| Found issue: Network calls must not block the main thread. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
URL(url).readText()
```
</details>

| ✅ | **#92 Async Net** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
async { URL(url).readText() }
```
</details>

| ✅ | **#93 Camera Perm** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
Camera.open()
```
</details>

| ✅ | **#94 Check Perm** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
if(checkPermission) Camera.open()
```
</details>

| ✅ | **#95 HTTP Conn** | Expected valid=False, got False \| Found issue: Network calls must not block the main thread. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
HttpURLConnection(url)
```
</details>

| ✅ | **#96 Location** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
LocationManager.get()
```
</details>

| ✅ | **#97 Contacts** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
ContactsContract.get()
```
</details>

| ✅ | **#98 UI Update** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
textView.setText('hi')
```
</details>

| ✅ | **#99 Toast** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
Toast.makeText()
```
</details>

| ✅ | **#100 Log** | Expected valid=True, got True |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
Log.d('tag', 'msg')
```
</details>

