#!/usr/bin/env python3
"""
Comprehensive test runner with report generation
"""

import unittest
import sys
from datetime import datetime
from pathlib import Path

def generate_report(result, output_file="test/reports/validation_test_report.md"):
    """Generate markdown test report"""
    
    # Ensure reports directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# P.DE.I Framework Validation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Summary:** {total_tests} Tests | ✅ {passed} Passed | ❌ {failures + errors} Failed\n\n")
        
        f.write("| Status | Test Case | Description |\n")
        f.write("| :---: | :--- | :--- |\n")
        
        # Write passed tests
        for test in result.successes if hasattr(result, 'successes') else []:
            test_name = test[0]._testMethodName
            test_doc = test[0]._testMethodDoc or "No description"
            f.write(f"| ✅ | {test_name} | {test_doc.strip()} |\n")
        
        # Write failed tests
        for test, traceback in result.failures:
            test_name = test._testMethodName
            test_doc = test._testMethodDoc or "No description"
            f.write(f"| ❌ | {test_name} | {test_doc.strip()} |\n")
        
        # Write error tests
        for test, traceback in result.errors:
            test_name = test._testMethodName
            test_doc = test._testMethodDoc or "No description"
            f.write(f"| ⚠️ | {test_name} | {test_doc.strip()} (ERROR) |\n")
        
        # Add detailed failure information if any
        if failures + errors > 0:
            f.write("\n## 🔍 Failure Details\n\n")
            
            for test, traceback in result.failures:
                f.write(f"### ❌ {test._testMethodName}\n\n")
                f.write("```\n")
                f.write(traceback)
                f.write("```\n\n")
            
            for test, traceback in result.errors:
                f.write(f"### ⚠️ {test._testMethodName}\n\n")
                f.write("```\n")
                f.write(traceback)
                f.write("```\n\n")
    
    print(f"\n📊 Test report generated: {output_file}")
    print(f"✅ {passed}/{total_tests} tests passed")
    
    return passed == total_tests

class CustomTestResult(unittest.TextTestResult):
    """Custom test result that tracks successes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successes = []
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append((test, ''))

def main():
    """Discover and run all tests, generate report"""
    
    print("🔍 Discovering tests in", Path(__file__).parent.absolute())
    
    # Discover all tests
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with custom result
    runner = unittest.TextTestRunner(
        verbosity=2,
        resultclass=CustomTestResult
    )
    result = runner.run(suite)
    
    # Generate report
    success = generate_report(result)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()