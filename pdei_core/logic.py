import logging
import re
from typing import Any, Dict, List, Tuple

class PDEIValidator:
    """
    P.DE.I Framework Core Validator
    
    Handles domain-specific code validation and rule enforcement.
    This class acts as a generic engine that applies rules defined in the domain configuration.
    """
    def __init__(self, domain_config: Dict[str, Any]):
        self.domain_config = domain_config
        # Default to generic if not specified
        self.domain = domain_config.get('domain', 'generic')
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load rules from the domain configuration."""
        # Expecting a dictionary of rule categories (e.g., "safety", "style")
        return self.domain_config.get('validation_rules', {})
    
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
        for rule in rules:
            # 1. Check Platform/Context constraints
            if 'platform' in rule:
                if rule['platform'].lower() not in context.lower():
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
                    if t in code or t.lower() in context.lower():
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
                    if pattern in code:
                        # Check exceptions
                        if 'exception' in rule and rule['exception'] in code:
                            continue
                            
                        issues.append(self._create_issue(rule, f"Forbidden pattern: {pattern}", code, pattern))

            # 4. Validate Required Patterns
            if 'required_pattern' in rule:
                pattern = rule['required_pattern']
                # Simple string check for now (could be upgraded to regex)
                if pattern not in code:
                    issues.append(self._create_issue(rule, f"Missing required pattern: {pattern}", code))

            # 5. Implicit Trigger Violation
            # If no explicit forbidden/required patterns, the trigger itself might be the issue
            # (e.g. "delay(" in non-blocking rule)
            if 'forbidden' not in rule and 'required_pattern' not in rule and 'trigger' in rule:
                for t in trigger_words:
                    if t in code:
                        if 'exception' in rule and rule['exception'] in code:
                            continue
                        issues.append(self._create_issue(rule, f"Issue detected: {t}", code, t))

        return issues

    def _create_issue(self, rule: Dict[str, Any], default_msg: str, code: str, pattern: str = None) -> Dict[str, Any]:
        issue = {
            "id": rule.get('id'),
            "severity": rule.get('severity', 'warning'),
            "message": rule.get('message', default_msg),
            "line": self._find_line(code, pattern) if pattern else -1
        }
        if 'auto_fix' in rule:
            issue['auto_fix'] = rule['auto_fix']
        return issue

    def _find_line(self, code: str, substring: str) -> int:
        for i, line in enumerate(code.splitlines(), 1):
            if substring in line:
                return i
        return -1