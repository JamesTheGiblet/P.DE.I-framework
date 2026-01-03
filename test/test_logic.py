import unittest
import sys
import os

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

if __name__ == '__main__':
    unittest.main()