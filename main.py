#!/usr/bin/env python3
"""
AI Executive v4.0 - Modular Entry Point
"""

import sys
import argparse
import logging
import socket
import uvicorn

# --- Import The Organs ---
from pdei_core.buddai_executive import BuddAI
from pdei_core.shared import APP_NAME, OLLAMA_HOST, OLLAMA_PORT, SERVER_AVAILABLE

# If server dependencies are present, import the app
if SERVER_AVAILABLE:
    from pdei_core.server import app
else:
    app = None

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(APP_NAME)

def check_ollama() -> bool:
    """Ensure the local brain (Ollama) is responsive."""
    import http.client
    try:
        conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=2)
        conn.request("GET", "/api/tags")
        return conn.getresponse().status == 200
    except:
        return False

def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except:
            return False

def main():
    if not check_ollama():
        print(f"❌ Ollama not running at {OLLAMA_HOST}:{OLLAMA_PORT}. Wake it up first!")
        sys.exit(1)

    parser = argparse.ArgumentParser(description=f"{APP_NAME} Executive v4.0")
    parser.add_argument("--server", action="store_true", help="Run in server mode")
    parser.add_argument("--port", type=int, default=8000, help="Port for server mode")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP address")
    parser.add_argument("--public-url", type=str, default="", help="Public URL for QR codes")
    parser.add_argument("--config", type=str, default="buddai_config.json", help="Path to main config file")
    parser.add_argument("--personality", type=str, help="Override personality file path")
    parser.add_argument("--domain", type=str, help="Override domain config file path")
    args = parser.parse_args()

    if args.server:
        if SERVER_AVAILABLE and app:
            port = args.port
            # Automatic port hunting logic
            if not is_port_available(port, args.host):
                print(f"⚠️ Port {port} in use, searching for available port...")
                for i in range(1, 11):
                    if is_port_available(port + i, args.host):
                        port += i
                        break

            # Silence health check noise
            class EndpointFilter(logging.Filter):
                def filter(self, record):
                    return "/api/system/status" not in record.getMessage()
            logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

            print(f"🚀 {APP_NAME} Exocortex Online: http://{args.host}:{port}/web")
            if args.public_url:
                app.state.public_url = args.public_url
                print(f"🔗 Public Tunnel: {args.public_url}")

            uvicorn.run(app, host=args.host, port=port)
        else:
            print("❌ Server dependencies missing. Install: fastapi, uvicorn, python-multipart")
    else:
        # Launch CLI Mode
        buddai = BuddAI(
            user_id="default", 
            server_mode=False,
            config_path=args.config,
            personality_path=args.personality,
            domain_config_path=args.domain
        )
        buddai.run()

if __name__ == "__main__":
    main()