import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path to allow importing pdei_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdei_core.logic import PDEIValidator

class TestForgeTheoryFixes(unittest.TestCase):
    def setUp(self):
        # Minimal config to instantiate validator
        self.config = {
            "domain": "forge_theory",
            "validation_rules": {
                "formulas": [
                    {
                        "id": "pid_dt_scaling",
                        "severity": "warning",
                        "message": "PID Integral terms should scale with time step (dt).",
                        "trigger": ["integral +=", "error_sum +="],
                        "forbidden": [],
                        "required_pattern": "dt",
                        "auto_fix": "fix_pid_dt"
                    }
                ]
            }
        }
        self.validator = PDEIValidator(self.config)

    def test_fix_decay_formula_structure(self):
        """Test conversion of (1 - exp(t/tau)) to exp(-t/tau)"""
        code = "voltage = 5 * (1 - exp(t/tau))"
        issue = {"auto_fix": "fix_decay_formula"}
        expected_snippet = "voltage = 5 * (exp(-t/tau))"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertIn(expected_snippet, fixed)

    def test_fix_decay_formula_positive_exponent(self):
        """Test conversion of exp(t/tau) to exp(-t/tau)"""
        code = "signal = exp(t/tau)"
        issue = {"auto_fix": "fix_decay_formula"}
        expected = "signal = exp(-t/tau)"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(expected, fixed)

    def test_fix_growth_formula_simple(self):
        """Test conversion of exp(-t/tau) to (1 - exp(-t/tau)) in growth context"""
        code = "heat_rise = exp(-t/tau)"
        issue = {"auto_fix": "fix_growth_formula"}
        expected = "heat_rise = (1 - exp(-t/tau))"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(expected, fixed)

    def test_fix_growth_formula_context_check(self):
        """Ensure fix only applies when context keywords (charge, heat, etc) are present"""
        # 'value' is not a trigger word defined in logic.py
        code = "value = exp(-t/tau)"
        issue = {"auto_fix": "fix_growth_formula"}
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(code, fixed)

    def test_fix_growth_formula_idempotency(self):
        """Ensure already correct formulas are not modified"""
        code = "charge = (1 - exp(-t/tau))"
        issue = {"auto_fix": "fix_growth_formula"}
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(code, fixed)

    def test_fix_step_response_structure(self):
        """Test conversion of step response with positive exponent to negative"""
        code = "position = target * (1 - exp(t/tau)) + start_pos"
        issue = {"auto_fix": "fix_step_response"}
        expected = "position = target * (1 - exp(-t/tau)) + start_pos"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(expected, fixed)

    def test_pid_dt_validation(self):
        """Test detection of missing dt in PID integral accumulation"""
        code = "integral += error; // Bad: Missing time scaling"
        
        # Validate should return False (invalid) and a list of issues
        valid, issues = self.validator.validate(code)
        
        # Check if our specific rule triggered
        self.assertTrue(any(i['id'] == 'pid_dt_scaling' for i in issues), "Failed to detect missing dt in PID loop")

    def test_fix_pid_dt_injection(self):
        """Test injection of * dt into integral accumulation"""
        code = "integral += error;"
        issue = {"auto_fix": "fix_pid_dt"}
        expected = "integral += error * dt;"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(expected, fixed)

    def test_forge_theory_global_enforcement(self):
        """Test that Forge Theory rules apply even in other domains (e.g. Pharma)"""
        pharma_config = {
            "domain": "pharma",
            "validation_rules": {}
        }
        validator = PDEIValidator(pharma_config)
        
        # Code violating a Forge Theory rule (Positive exponent decay)
        # Must include trigger word like 'decay' or 'cool'
        code = "cooling_rate = exp(t/tau)"
        
        valid, issues = validator.validate(code)
        
        # Check if Forge Theory rule triggered
        self.assertTrue(any(i.get('id') == 'decay_negative_exponent' for i in issues), 
                       "Forge Theory rules should be globally enforced")

    def test_inline_forge_math_check(self):
        """Test that abstracted Forge math is flagged"""
        code = "void applyDecay() { return exp(-t/tau); }"
        valid, issues = self.validator.validate(code)
        self.assertTrue(any(i['id'] == 'inline_forge_math' for i in issues))

    def test_ldr_smoothing_check(self):
        """Test LDR smoothing formula enforcement"""
        # Bad: Linear average
        code_bad = "ldrValue = (ldrValue + raw) / 2;" 
        valid, issues = self.validator.validate(code_bad, context="ldr sensor")
        self.assertTrue(any(i['id'] == 'ldr_smoothing_formula' for i in issues))

        # Good: Alpha filter
        code_good = "ldrValue = ldrValue * (1 - alpha) + raw * alpha;"
        valid, issues = self.validator.validate(code_good, context="ldr sensor")
        self.assertTrue(valid)

class MarkdownTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append({
            "name": test._testMethodName,
            "doc": test._testMethodDoc or "",
            "status": "PASS"
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append({
            "name": test._testMethodName,
            "doc": test._testMethodDoc or "",
            "status": "FAIL"
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append({
            "name": test._testMethodName,
            "doc": test._testMethodDoc or "",
            "status": "ERROR"
        })

if __name__ == '__main__':
    # Load tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestForgeTheoryFixes)
    
    # Run with custom result handler
    runner = unittest.TextTestRunner(resultclass=MarkdownTestResult, verbosity=2)
    result = runner.run(suite)

    # Generate Report
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_path = os.path.join(os.path.dirname(__file__), "logic_test_report.md")
    
    total = result.testsRun
    passed = len([r for r in result.test_results if r['status'] == 'PASS'])
    failed = total - passed
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Logic System Test Report\n\n")
        f.write(f"**Date:** {timestamp}\n")
        f.write(f"**Summary:** {total} Tests | ✅ {passed} Passed | ❌ {failed} Failed\n\n")
        f.write("| Status | Test Case | Description |\n| :---: | :--- | :--- |\n")
        for r in result.test_results:
            icon = "✅" if r['status'] == "PASS" else "❌"
            doc = r['doc'].strip().split('\n')[0] if r['doc'] else "No description"
            f.write(f"| {icon} | **{r['name']}** | {doc} |\n")
            
    print(f"\n📄 Report generated: {report_path}")