import unittest
import sys
import os
from datetime import datetime

# Add project root to path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

class MarkdownTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append({
            "name": str(test),
            "doc": test._testMethodDoc or "",
            "status": "PASS"
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append({
            "name": str(test),
            "doc": test._testMethodDoc or "",
            "status": "FAIL",
            "error": str(err[1])
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append({
            "name": str(test),
            "doc": test._testMethodDoc or "",
            "status": "ERROR",
            "error": str(err[1])
        })

if __name__ == '__main__':
    # Discover tests in all subdirectories
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"🔍 Discovering tests in {start_dir}...")
    # Discover all test_*.py files recursively
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run with custom result handler
    runner = unittest.TextTestRunner(resultclass=MarkdownTestResult, verbosity=2)
    result = runner.run(suite)

    # Generate Report
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_path = os.path.join(start_dir, "validation_test_report.md")
    
    total = result.testsRun
    passed = len([r for r in result.test_results if r['status'] == 'PASS'])
    failed = total - passed
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# P.DE.I Framework Validation Report\n\n")
        f.write(f"**Date:** {timestamp}\n")
        f.write(f"**Summary:** {total} Tests | ✅ {passed} Passed | ❌ {failed} Failed\n\n")
        f.write("| Status | Test Case | Description |\n| :---: | :--- | :--- |\n")
        for r in result.test_results:
            icon = "✅" if r['status'] == "PASS" else "❌"
            # Format name: test_method (module.Class) -> module.Class.test_method
            name_parts = r['name'].split(' ')
            test_method = name_parts[0]
            test_class = name_parts[1].strip('()') if len(name_parts) > 1 else ""
            
            doc = r['doc'].strip().split('\n')[0] if r['doc'] else "No description"
            f.write(f"| {icon} | **{test_method}**<br><small>{test_class}</small> | {doc} |\n")
            
    print(f"\n📄 Report generated: {report_path}")