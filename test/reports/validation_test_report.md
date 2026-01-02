# P.DE.I Validation Test Report

# ❌ FAILED

**Date:** 2026-01-02 22:41:44
**Summary:** 30 Tests | ✅ 26 Passed | ❌ 4 Failed | **86.7% Pass Rate**

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

| ❌ | **#3 Safety Timeout** | Expected valid=False, got False \| Found issue: Critical: No safety timeout detected (must be > 500ms). \| Auto-fix failed. Result: digitalWrite(M1, HIGH); |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
digitalWrite(M1, HIGH);
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

| ❌ | **#9 Clean Motor** | Expected valid=True, got False |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
if(safe) digitalWrite(M1, H);
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

| ❌ | **#19 Comment Ignore** | Expected valid=True, got False |

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

| ❌ | **#22 ADA Compliant** | Expected valid=True, got False |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
door_width = 36
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

