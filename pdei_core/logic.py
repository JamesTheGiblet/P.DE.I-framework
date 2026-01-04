#!/usr/bin/env python3
"""
C:\Users\gilbe\Documents\GitHub\readme-hub\P.DE.I-framework\pdei_core\logic.py
P.DE.I Framework - Logic & Validation Engine
============================================

This module defines the `PDEIValidator` class, which serves as the Quality Assurance (QA) layer
for the P.DE.I framework. It enforces domain-specific rules, safety constraints (Forge Theory),
and coding standards on all AI-generated code.

Key Responsibilities:
1. Rule Management: Loads and merges validation rules from domain configurations and the core Forge Theory.
2. Static Analysis: Scans code for forbidden patterns, missing safeguards, and context-specific violations.
3. Auto-Correction: Capable of automatically fixing critical safety issues (e.g., injecting timeouts, correcting mathematical formulas).
4. Compliance: Enforces industry-specific standards (e.g., ADA compliance, Pharma audit logging).

Where it fits:
    This module is imported by `buddai_executive.py`. It is invoked immediately after the LLM generates code
    to validate, sanitize, and potentially auto-repair the output before it is shown to the user.
"""
import logging
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

class PDEIValidator:
    """
    P.DE.I Framework Core Validator
    
    Handles domain-specific code validation and rule enforcement.
    This class acts as a generic engine that applies rules defined in the domain configuration.
    """
    def __init__(self, domain_config: Dict[str, Any], memory_interface: Any = None):
        self.domain_config = domain_config
        self.memory_interface = memory_interface
        # Default to generic if not specified
        self.domain = domain_config.get('domain', 'generic')
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load rules from the domain configuration and merge with Fundamental Forge Theory."""
        # Start with domain specific rules (copying to avoid mutation)
        source_rules = self.domain_config.get('validation_rules', {})
        rules = {k: v[:] for k, v in source_rules.items()}
        
        # Load Fundamental Forge Theory Rules
        try:
            root_dir = Path(__file__).parent.parent
            forge_path = root_dir / "domain_configs" / "forge_theory.json"
            
            if forge_path.exists():
                with open(forge_path, 'r', encoding='utf-8') as f:
                    forge_config = json.load(f)
                    forge_rules = forge_config.get('validation_rules', {})
                    
                    for category, cat_rules in forge_rules.items():
                        if category not in rules:
                            rules[category] = []
                        
                        suppressed_ids = self.domain_config.get('suppressed_rules', [])

                        # Merge: Add Forge rule if ID not present in Domain rules
                        existing_ids = {r.get('id') for r in rules[category] if 'id' in r}
                        for rule in cat_rules:
                            if rule.get('id') not in existing_ids and rule.get('id') not in suppressed_ids:
                                rules[category].append(rule)

            # Load Learned Rules from Memory (The "Graduation" Link)
            if self.memory_interface:
                try:
                    learned_rules = self.memory_interface.get_learned_rules(min_confidence=0.85)
                    if learned_rules:
                        if 'learned_behavior' not in rules:
                            rules['learned_behavior'] = []
                        
                        for idx, rule in enumerate(learned_rules):
                            rules['learned_behavior'].append({
                                "id": f"learned_{idx}",
                                "severity": "warning",
                                "message": f"Learned Violation: {rule['rule']}",
                                "forbidden_regex": [rule['find']],
                                "auto_fix": "generic_regex_replace",
                                "replacement": rule['replace']
                            })
                except Exception as e:
                    logging.warning(f"Failed to load learned rules: {e}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to load Fundamental Forge Theory: {e}")

        return rules
    
    def validate(self, code: str, context: str = "") -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate generated code against domain rules.
        
        Args:
            code: The source code to validate
            context: Additional context (user message, hardware profile, etc.)
            
        Returns:
            Tuple containing (is_valid: bool, issues: List[Dict])
        """
        issues = []
        
        # Iterate through all rule categories (safety, style, etc.)
        for category, rules in self.validation_rules.items():
            if isinstance(rules, list):
                issues.extend(self._check_rules(code, context, rules))
        
        return len([i for i in issues if i.get('severity') == 'error']) == 0, issues

    def _check_rules(self, code: str, context: str, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generic rule checker engine."""
        issues = []
        clean_code = self._strip_comments(code)
        
        for rule in rules:
            # 1. Check Platform/Context constraints
            if 'platform' in rule:
                if rule['platform'].lower() not in context.lower():
                    continue

            # 1.5 Check Excluded Context
            if 'exclude_context' in rule:
                exclusions = rule['exclude_context']
                if isinstance(exclusions, str):
                    exclusions = [exclusions]
                
                # If any exclusion term is found in code or context, skip this rule
                if any(ex in clean_code or ex.lower() in context.lower() for ex in exclusions):
                    continue

            # 2. Check Triggers
            # If triggers exist, at least one must be present in code OR context
            triggered = True
            trigger_words = []
            if 'trigger' in rule:
                trigger_words = rule['trigger']
                if isinstance(trigger_words, str):
                    trigger_words = [trigger_words]
                
                found_trigger = False
                for t in trigger_words:
                    if t in clean_code or t.lower() in context.lower():
                        found_trigger = True
                        break
                if not found_trigger:
                    triggered = False
            
            if not triggered:
                continue

            # 3. Validate Forbidden Patterns
            if 'forbidden' in rule:
                forbidden = rule['forbidden']
                if isinstance(forbidden, str):
                    forbidden = [forbidden]
                
                for pattern in forbidden:
                    if pattern in clean_code:
                        # Check exceptions
                        if 'exception' in rule and rule['exception'] in code:
                            continue
                            
                        issues.append(self._create_issue(rule, f"Forbidden pattern: {pattern}", code, pattern))

            # 3.5 Validate Forbidden Regex (For Learned Rules)
            if 'forbidden_regex' in rule:
                forbidden_re = rule['forbidden_regex']
                if isinstance(forbidden_re, str):
                    forbidden_re = [forbidden_re]
                
                for pattern in forbidden_re:
                    if re.search(pattern, clean_code):
                        issues.append(self._create_issue(rule, f"Forbidden pattern (regex): {pattern}", code, pattern, is_regex=True))

            # 4. Validate Required Patterns
            if 'required_pattern' in rule:
                pattern = rule['required_pattern']
                # Simple string check for now (could be upgraded to regex)
                if pattern not in clean_code:
                    issues.append(self._create_issue(rule, f"Missing required pattern: {pattern}", code))

            # 4.5 Validate Required Regex
            if 'required_regex' in rule:
                pattern = rule['required_regex']
                if not re.search(pattern, clean_code):
                    issues.append(self._create_issue(rule, f"Missing required pattern (regex): {pattern}", code))

            # 5. Implicit Trigger Violation
            # If no explicit forbidden/required patterns, the trigger itself might be the issue
            # (e.g. "delay(" in non-blocking rule)
            if 'forbidden' not in rule and 'required_pattern' not in rule and 'trigger' in rule:
                for t in trigger_words:
                    if t in clean_code:
                        if 'exception' in rule and rule['exception'] in code:
                            continue
                        issues.append(self._create_issue(rule, f"Issue detected: {t}", code, t))

        return issues

    def _create_issue(self, rule: Dict[str, Any], default_msg: str, code: str, pattern: str = None, is_regex: bool = False) -> Dict[str, Any]:
        issue = {
            "id": rule.get('id'),
            "severity": rule.get('severity', 'warning'),
            "message": rule.get('message', default_msg),
            "line": self._find_line(code, pattern, is_regex) if pattern else -1,
            "trigger_pattern": pattern
        }
        if 'auto_fix' in rule:
            issue['auto_fix'] = rule['auto_fix']
        if 'replacement' in rule:
            issue['replacement'] = rule['replacement']
        return issue

    def _find_line(self, code: str, substring: str, is_regex: bool = False) -> int:
        for i, line in enumerate(code.splitlines(), 1):
            if is_regex:
                if re.search(substring, line):
                    return i
            elif substring in line:
                return i
        return -1

    def _strip_comments(self, code: str) -> str:
        """Remove comments to prevent false positives in validation."""
        # Remove C-style block comments /* ... */
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        # Remove // comments and # comments
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'#.*', '', code)
        return code

    def auto_fix(self, code: str, issues: List[Dict[str, Any]]) -> str:
        """Apply all auto-fixes and return corrected code"""
        fixed_code = code
        for issue in issues:
            if 'auto_fix' in issue:
                fixed_code = self._apply_fix(fixed_code, issue['auto_fix'], issue)
        return fixed_code

    def _apply_fix(self, code: str, fix_type: str, issue: Dict[str, Any]) -> str:
        """Dispatcher for specific fix logic."""
        if fix_type == "inject_safety_timeout":
            return self._fix_inject_safety_timeout(code)
        elif fix_type == "esp32_pwm_fix":
            return self._fix_esp32_pwm(code)
        elif fix_type == "esp32_adc_fix":
            return self._fix_esp32_adc(code)
        elif fix_type == "inject_audit_header":
            return self._fix_pharma_audit_header(code)
        elif fix_type == "fix_ada_compliance":
            return self._fix_ada_compliance(code)
        elif fix_type == "fix_decay_formula":
            return self._fix_decay_formula(code, issue)
        elif fix_type == "fix_growth_formula":
            return self._fix_growth_formula(code, issue)
        elif fix_type == "fix_step_response":
            return self._fix_step_response(code, issue)
        elif fix_type == "fix_pid_dt":
            return self._fix_pid_dt(code, issue)
        elif fix_type == "generic_regex_replace":
            return self._fix_generic_regex(code, issue)
        return code

    def _fix_inject_safety_timeout(self, code: str) -> str:
        """Inject a safety timeout check into the loop."""
        if "SAFETY_TIMEOUT" in code: return code
        
        # 1. Inject globals
        if "void setup" in code:
            code = code.replace("void setup", "unsigned long lastCommand = 0;\nconst long SAFETY_TIMEOUT = 500;\n\nvoid setup")
            
        # 2. Inject check in loop
        if "void loop() {" in code:
            injection = "\n  if (millis() - lastCommand > SAFETY_TIMEOUT) {\n    // Failsafe triggered\n  }\n"
            code = code.replace("void loop() {", "void loop() {" + injection)
            
        return code

    def _fix_esp32_pwm(self, code: str) -> str:
        """Replace analogWrite with ledcWrite for ESP32."""
        return code.replace("analogWrite", "ledcWrite")

    def _fix_esp32_adc(self, code: str) -> str:
        """Update ADC resolution from 10-bit to 12-bit."""
        return code.replace("1023", "4095").replace("1024", "4096")

    def _fix_pharma_audit_header(self, code: str) -> str:
        """Inject @audit_log decorator for Pharma compliance."""
        lines = code.splitlines()
        fixed_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                # Check if @audit_log is already present in the previous line
                if not (fixed_lines and "@audit_log" in fixed_lines[-1]):
                    # Match indentation
                    indent = line[:len(line) - len(stripped)]
                    fixed_lines.append(f"{indent}@audit_log")
            fixed_lines.append(line)
        return "\n".join(fixed_lines)

    def _fix_ada_compliance(self, code: str) -> str:
        """Ensure width assignments meet ADA minimums (36 inches)."""
        keywords = ["door", "ramp", "corridor", "hallway", "width"]
        
        def replace_width(match):
            var_name = match.group(1)
            if not any(k in var_name.lower() for k in keywords):
                return match.group(0)
                
            val = int(match.group(2))
            if val < 36:
                return f"{var_name} = 36; // Auto-fixed for ADA (was {val})"
            return match.group(0)
        
        # Match any assignment: var = number
        return re.sub(r'([a-zA-Z0-9_]+)\s*=\s*(\d+)', replace_width, code)

    def _fix_decay_formula(self, code: str, issue: Dict[str, Any]) -> str:
        """Convert incorrect decay formulas to exp(-t/tau) form."""
        # Fix: (1 - exp(t/tau)) -> exp(-t/tau)
        # Regex captures content inside exp(...) as group 1
        code = re.sub(r'1\s*-\s*exp\(([^)]+)\)', r'exp(-\1)', code)
        
        # Fix: exp(t/tau) -> exp(-t/tau)
        # Regex looks for exp(t/...) and captures the denominator (tau) as group 1
        code = re.sub(r'exp\(\s*t\s*/\s*([^)]+)\)', r'exp(-t/\1)', code)
        return code

    def _fix_growth_formula(self, code: str, issue: Dict[str, Any]) -> str:
        """Convert incorrect growth formulas to (1 - exp(-t/tau)) form."""
        lines = code.splitlines()
        fixed = []
        for line in lines:
            # If line has exp(-t/tau) but no (1 - ...), wrap it
            if 'exp(-' in line and '(1 -' not in line:
                # Check context
                if any(word in line.lower() for word in ['charge', 'heat', 'rise', 'grow']):
                    line = re.sub(r'=\s*([^;]*?exp\([^)]+\))', r'= (1 - \1)', line)
            fixed.append(line)
        return '\n'.join(fixed)

    def _fix_step_response(self, code: str, issue: Dict[str, Any]) -> str:
        """Fix sign in step response: (1 - exp(t/tau)) -> (1 - exp(-t/tau))"""
        # Regex matches (1 - exp(t/tau)) and captures tau
        return re.sub(r'\(1\s*-\s*exp\(\s*t\s*/\s*([^)]+)\)\)', r'(1 - exp(-t/\1))', code)

    def _fix_pid_dt(self, code: str, issue: Dict[str, Any]) -> str:
        """Inject * dt into PID integral terms."""
        lines = code.splitlines()
        fixed = []
        triggers = ["integral +=", "error_sum +="]
        for line in lines:
            if any(t in line for t in triggers) and "dt" not in line:
                # Append * dt before the semicolon if present
                if ";" in line:
                    line = line.replace(";", " * dt;")
                else:
                    line = line + " * dt"
            fixed.append(line)
        return "\n".join(fixed)

    def _fix_generic_regex(self, code: str, issue: Dict[str, Any]) -> str:
        """Apply a generic regex replacement from a learned rule."""
        pattern = issue.get('trigger_pattern')
        replacement = issue.get('replacement')
        if pattern and replacement:
            return re.sub(pattern, replacement, code)
        return code