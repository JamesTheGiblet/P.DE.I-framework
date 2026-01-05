import urllib.request
import json
import sys

def test_daemon():
    url = "http://localhost:8000"
    # You can change this message to test different personas
    payload = {"message": "System status check"}
    
    print(f"📡 Connecting to Exocortex Daemon at {url}...")
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                body = json.loads(response.read().decode())
                print("\n✅ Daemon Response:")
                print(json.dumps(body, indent=2))
            else:
                print(f"⚠️ HTTP {response.status}")
                
    except urllib.error.URLError as e:
        print(f"❌ Connection Failed: {e}")
        print("   (Ensure 'python scripts/init_exocortex.py --daemon' is running in another terminal)")

if __name__ == "__main__":
    test_daemon()