import requests
import sys
import time

def check_server(url="http://localhost:8000"):
    print(f"🔍 Checking Server Health at {url}...")
    try:
        # 1. Root Endpoint (HTML Dashboard)
        start = time.time()
        r = requests.get(f"{url}/")
        latency = (time.time() - start) * 1000
        
        if r.status_code == 200:
            print(f"✅ Root Endpoint: OK ({latency:.1f}ms)")
        else:
            print(f"❌ Root Endpoint: Failed ({r.status_code})")
            
        # 2. System Status (JSON API)
        r = requests.get(f"{url}/api/system/status")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ System Status: OK (CPU: {data.get('cpu')}%, Mem: {data.get('memory')}%)")
        else:
            print(f"❌ System Status: Failed ({r.status_code})")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("👉 Ensure the server is running via 'python launch.py'")

if __name__ == "__main__":
    check_server()