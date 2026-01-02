# P.DE.I Validation Test Report

**Date:** 2026-01-02 22:12:01
**Summary:** 12 Tests | ✅ 12 Passed | ❌ 0 Failed | **100.0% Pass Rate**

## Detailed Results

### Setup

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **Load Domain Config** |  |
| ✅ | **Initialize Validator** |  |
### Safety

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **Detect Blocking Delay** | Found: Blocking delay() detected. Prefer non-blocking logic. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void loop() {
        digitalWrite(LED, HIGH);
        delay(1000); // Bad
    }
```
</details>

| ✅ | **Detect Missing Safety Timeout** | Found: Critical: No safety timeout detected (must be > 500ms). |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void loop() {
        // Motor control without timeout
        digitalWrite(MOTOR_PIN, HIGH);
    }
```
</details>

### Hardware

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **Detect ESP32 analogWrite** | Found: ESP32 does not support analogWrite. Use ledcWrite instead. |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
analogWrite(PIN, 128);
```
</details>

| ✅ | **Detect ESP32 10-bit ADC** | Found: ESP32 ADC resolution is 12-bit (4095), not 10-bit (1023/1024). |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
int val = map(x, 0, 1023, 0, 255);
```
</details>

| ✅ | **Allow analogWrite on Arduino** | Issues found: [] |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
analogWrite(PIN, 128);
```
</details>

### Auto-Fix

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **Fix ESP32 ADC Resolution** | Expected 4095, got: int val = map(x, 0, 4095, 0, 255); |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
int val = map(x, 0, 1023, 0, 255);
```
**Output/Fix:**
```cpp
int val = map(x, 0, 4095, 0, 255);
```
</details>

| ✅ | **Inject Safety Timeout** | Checked for SAFETY_TIMEOUT constant and logic |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
void setup() {
  pinMode(M1, OUTPUT);
}
void loop() {
  digitalWrite(M1, HIGH);
}
```
**Output/Fix:**
```cpp
unsigned long lastCommand = 0;
const long SAFETY_TIMEOUT = 500;

void setup() {
  pinMode(M1, OUTPUT);
}
void loop() {
  if (millis() - lastCommand > SAFETY_TIMEOUT) {
    // Failsafe triggered
  }

  digitalWrite(M1, HIGH);
}
```
</details>

### Pharma

| Status | Test Case | Details |
| :---: | :--- | :--- |
| ✅ | **Detect Missing Audit Header** | Found: Missing audit log decorator |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def calculate_dose(w): return w*2
```
</details>

| ✅ | **Inject Audit Header** | Checked for @audit_log decorator |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
def calculate_dose(w): return w*2
```
**Output/Fix:**
```cpp
@audit_log
def calculate_dose(w): return w*2
```
</details>

| ✅ | **Respect Existing Header** | Issues found: [] |

<details><summary>View Code Diff</summary>

**Input:**
```cpp
@audit_log
def existing_func(): pass
```
</details>

