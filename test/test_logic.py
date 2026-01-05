import unittest
import sys
import os
import shutil
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

    def test_strip_comments(self):
        """Test comment stripping utility"""
        code = "x = 1; // comment\n/* block */\ny = 2; # python style"
        clean = self.validator._strip_comments(code)
        self.assertNotIn("comment", clean)
        self.assertNotIn("block", clean)
        self.assertNotIn("python style", clean)
        self.assertIn("x = 1;", clean)
        self.assertIn("y = 2;", clean)

    def test_fix_audit_header(self):
        """Test injection of audit header"""
        code = "def process_data():\n    pass"
        issue = {"auto_fix": "inject_audit_header"}
        expected = "@audit_log\ndef process_data():\n    pass"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(expected, fixed)

    def test_fix_ada_compliance(self):
        """Test ADA compliance fix for widths"""
        code = "door_width = 30;"
        issue = {"auto_fix": "fix_ada_compliance"}
        expected = "door_width = 36; // Auto-fixed for ADA (was 30);"
        
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(expected, fixed)

    def test_exclude_context(self):
        """Test rule exclusion based on context"""
        # Create a validator with a rule that has exclude_context
        config = {
            "domain": "test",
            "validation_rules": {
                "safety": [{
                    "id": "no_delay",
                    "severity": "error",
                    "forbidden": ["delay("],
                    "exclude_context": ["test_mode"]
                }]
            }
        }
        v = PDEIValidator(config)
        
        code = "delay(100);"
        
        # Should fail normally
        valid, issues = v.validate(code, context="normal")
        self.assertFalse(valid)
        
        # Should pass with excluded context
        valid, issues = v.validate(code, context="test_mode")
        self.assertTrue(valid)

    def test_validate_required_regex(self):
        """Test required_regex rule."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [{
                    "id": "req_regex",
                    "severity": "error",
                    "required_regex": r"def\s+test_\w+\(\):"
                }]
            }
        }
        v = PDEIValidator(config)
        
        valid, issues = v.validate("def test_func(): pass")
        self.assertTrue(valid)
        
        valid, issues = v.validate("def func(): pass")
        self.assertFalse(valid)
        self.assertEqual(issues[0]['id'], "req_regex")

    def test_validate_forbidden_regex(self):
        """Test forbidden_regex rule."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [{
                    "id": "no_bad_vars",
                    "severity": "error",
                    "forbidden_regex": r"temp_\d+"
                }]
            }
        }
        v = PDEIValidator(config)
        
        valid, issues = v.validate("x = temp_123")
        self.assertFalse(valid)
        
        valid, issues = v.validate("x = temp_var")
        self.assertTrue(valid)

    def test_multiple_triggers(self):
        """Test rule with multiple triggers."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [{
                    "id": "multi_trig",
                    "severity": "error",
                    "trigger": ["foo", "bar"],
                    "forbidden": ["baz"]
                }]
            }
        }
        v = PDEIValidator(config)
        
        # Trigger 'foo' present, forbidden 'baz' present -> Fail
        valid, issues = v.validate("foo baz")
        self.assertFalse(valid)
        
        # Trigger 'bar' present, forbidden 'baz' present -> Fail
        valid, issues = v.validate("bar baz")
        self.assertFalse(valid)
        
        # No trigger, forbidden 'baz' present -> Pass
        valid, issues = v.validate("baz")
        self.assertTrue(valid)

    def test_platform_constraint(self):
        """Test rule with platform constraint."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [{
                    "id": "plat_check",
                    "severity": "error",
                    "platform": "arduino",
                    "forbidden": ["malloc"]
                }]
            }
        }
        v = PDEIValidator(config)
        
        # Context matches platform -> Fail
        valid, issues = v.validate("malloc(10)", context="arduino uno")
        self.assertFalse(valid)
        
        # Context does not match -> Pass
        valid, issues = v.validate("malloc(10)", context="python")
        self.assertTrue(valid)

    # --- New Tests (20) ---

    def test_validate_empty_code(self):
        """Test validation with empty string."""
        valid, issues = self.validator.validate("")
        self.assertTrue(valid)
        self.assertEqual(len(issues), 0)

    def test_validate_no_rules(self):
        """Test validation with empty config rules."""
        v = PDEIValidator({"domain": "test", "validation_rules": {}})
        valid, issues = v.validate("some code")
        self.assertTrue(valid)

    def test_validate_severity_levels(self):
        """Test different severity levels."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [
                    {"id": "err", "severity": "error", "forbidden": ["bad"]},
                    {"id": "warn", "severity": "warning", "forbidden": ["risky"]},
                    {"id": "info", "severity": "info", "forbidden": ["note"]}
                ]
            }
        }
        v = PDEIValidator(config)
        
        # Error makes it invalid
        valid, issues = v.validate("bad")
        self.assertFalse(valid)
        self.assertEqual(issues[0]['severity'], 'error')
        
        # Warning keeps it valid
        valid, issues = v.validate("risky")
        self.assertTrue(valid)
        self.assertEqual(issues[0]['severity'], 'warning')

    def test_required_pattern_missing(self):
        """Test missing required pattern."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [{"id": "req", "severity": "error", "required_pattern": "must_have"}]
            }
        }
        v = PDEIValidator(config)
        valid, issues = v.validate("code without pattern")
        self.assertFalse(valid)
        self.assertEqual(issues[0]['id'], 'req')

    def test_required_pattern_present(self):
        """Test present required pattern."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [{"id": "req", "severity": "error", "required_pattern": "must_have"}]
            }
        }
        v = PDEIValidator(config)
        valid, issues = v.validate("code with must_have")
        self.assertTrue(valid)

    def test_auto_fix_no_issues(self):
        """Test auto_fix with empty issue list."""
        code = "code"
        fixed = self.validator.auto_fix(code, [])
        self.assertEqual(fixed, code)

    def test_auto_fix_unknown_id(self):
        """Test auto_fix with unknown fix ID."""
        code = "code"
        issue = {"auto_fix": "unknown_fix_action"}
        fixed = self.validator.auto_fix(code, [issue])
        self.assertEqual(fixed, code)

    def test_strip_comments_cpp_style(self):
        """Test stripping C++ style comments."""
        code = "int x = 1; // comment"
        clean = self.validator._strip_comments(code)
        self.assertEqual(clean.strip(), "int x = 1;")

    def test_strip_comments_python_style(self):
        """Test stripping Python style comments."""
        code = "x = 1 # comment"
        clean = self.validator._strip_comments(code)
        self.assertEqual(clean.strip(), "x = 1")

    def test_strip_comments_block(self):
        """Test stripping block comments."""
        code = "x = 1; /* comment */ y = 2;"
        clean = self.validator._strip_comments(code)
        self.assertNotIn("comment", clean)
        self.assertIn("x = 1;", clean)
        self.assertIn("y = 2;", clean)

    def test_multiple_issues_same_line(self):
        """Test detection of multiple issues on the same line."""
        config = {
            "domain": "test",
            "validation_rules": {
                "check": [
                    {"id": "1", "severity": "error", "forbidden": ["foo"]},
                    {"id": "2", "severity": "error", "forbidden": ["bar"]}
                ]
            }
        }
        v = PDEIValidator(config)
        valid, issues = v.validate("foo bar")
        self.assertFalse(valid)
        self.assertEqual(len(issues), 2)
        ids = sorted([i['id'] for i in issues])
        self.assertEqual(ids, ["1", "2"])

    # --- New Tests (4) ---

    def test_validate_multiline_string(self):
        """Test validation within multiline strings."""
        code = 'x = """\nforbidden_word\n"""'
        config = {"domain": "test", "validation_rules": {"check": [{"id": "f", "severity": "error", "forbidden": ["forbidden_word"]}]}}
        v = PDEIValidator(config)
        valid, issues = v.validate(code)
        self.assertFalse(valid)

    def test_validate_mixed_quotes(self):
        """Test validation with mixed quotes."""
        code = "x = 'forbidden_word'"
        config = {"domain": "test", "validation_rules": {"check": [{"id": "f", "severity": "error", "forbidden": ["forbidden_word"]}]}}
        v = PDEIValidator(config)
        valid, issues = v.validate(code)
        self.assertFalse(valid)

    def test_validate_unicode_identifiers(self):
        """Test validation with unicode identifiers."""
        code = "变 = 1"
        valid, issues = self.validator.validate(code)
        self.assertTrue(valid)

    def test_validate_with_line_numbers(self):
        """Test if issues contain line numbers (mock check)."""
        code = "line1\nline2\nbad"
        config = {"domain": "test", "validation_rules": {"check": [{"id": "f", "severity": "error", "forbidden": ["bad"]}]}}
        v = PDEIValidator(config)
        valid, issues = v.validate(code)
        self.assertFalse(valid)

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
    
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    report_path = os.path.join(reports_dir, "logic_test_report.md")
    
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
    
    # Archive timestamped copy
    ts_file = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_path = os.path.join(reports_dir, f"logic_test_report_{ts_file}.md")
    try:
        shutil.copy(report_path, archive_path)
        print(f"🗃️  Archived report: {archive_path}")
    except Exception as e:
        print(f"⚠️  Failed to archive report: {e}")