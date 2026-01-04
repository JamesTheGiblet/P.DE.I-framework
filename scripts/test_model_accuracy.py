import argparse
import json
import http.client
import sys
import os
import time

# Configuration
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434

def query_ollama(model, prompt):
    conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=60)
    headers = {"Content-Type": "application/json"}
    
    # Use chat endpoint as models are likely chat-tuned
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0} # Deterministic for testing
    }
    
    try:
        conn.request("POST", "/api/chat", json.dumps(body), headers)
        response = conn.getresponse()
        if response.status == 200:
            data = json.loads(response.read().decode('utf-8'))
            return data.get("message", {}).get("content", "")
        else:
            print(f"Error: {response.status} - {response.read().decode('utf-8')}")
            return ""
    except Exception as e:
        print(f"Connection Error: {e}")
        return ""
    finally:
        conn.close()

def run_tests(model_name, tests):
    print(f"\n🧪 Testing Model: {model_name}")
    print("-" * 60)
    
    passed = 0
    total = len(tests)
    results = []
    
    for i, test in enumerate(tests, 1):
        prompt = test['prompt']
        expected = test.get('expected_formula')
        forbidden = test.get('forbidden_patterns', [])
        
        print(f"[{i}/{total}] Prompt: {prompt[:50]}...")
        
        response = query_ollama(model_name, prompt)
        
        if not response:
            print("  ❌ No response from model")
            results.append(False)
            continue
            
        # Checks
        check_pass = True
        reasons = []
        
        # Normalize strings for comparison (remove spaces) to avoid trivial formatting failures
        response_norm = response.replace(" ", "").replace("\n", "")
        expected_norm = expected.replace(" ", "") if expected else ""
        
        if expected and expected_norm not in response_norm:
            check_pass = False
            reasons.append(f"Missing expected: '{expected}'")
            
        for bad in forbidden:
            if bad in response:
                check_pass = False
                reasons.append(f"Found forbidden: '{bad}'")
                
        if check_pass:
            print("  ✅ PASS")
            passed += 1
            results.append(True)
        else:
            print(f"  ❌ FAIL: {', '.join(reasons)}")
            print(f"     Response: {response.strip().replace(chr(10), ' ')[:300]}...")
            results.append(False)
            
    accuracy = (passed / total) * 100 if total > 0 else 0
    print("-" * 60)
    print(f"📊 Accuracy: {accuracy:.1f}% ({passed}/{total})")
    return accuracy

def main():
    parser = argparse.ArgumentParser(description="Test LLM accuracy against defined patterns")
    parser.add_argument("--model", required=True, help="Model to test")
    parser.add_argument("--tests", default="test/model_accuracy_test.json", help="JSON file containing test cases")
    parser.add_argument("--baseline", help="Optional baseline model to compare against")
    parser.add_argument("--host", default="127.0.0.1", help="Ollama host IP")
    parser.add_argument("--port", type=int, default=11434, help="Ollama port")
    
    args = parser.parse_args()
    
    global OLLAMA_HOST, OLLAMA_PORT
    OLLAMA_HOST = args.host
    OLLAMA_PORT = args.port
    
    if not os.path.exists(args.tests):
        print(f"Error: Test file not found: {args.tests}")
        sys.exit(1)
        
    with open(args.tests, 'r') as f:
        tests = json.load(f)
        
    print(f"Loaded {len(tests)} test cases from {args.tests}")
    
    # Test Target Model
    target_acc = run_tests(args.model, tests)
    
    # Test Baseline if provided
    if args.baseline:
        base_acc = run_tests(args.baseline, tests)
        
        diff = target_acc - base_acc
        print(f"\n📈 Improvement over baseline: {diff:+.1f}%")
        if diff > 0:
            print("🎉 The new model is better!")
        elif diff < 0:
            print("⚠️ The new model performed worse.")
        else:
            print("😐 No change in accuracy.")

if __name__ == "__main__":
    main()