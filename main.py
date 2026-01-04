#!/usr/bin/env python3
"""
C:\Users\gilbe\Documents\GitHub\readme-hub\P.DE.I-framework\main.py
P.DE.I Framework - Main Executive Runtime
=========================================

This script serves as the primary runtime entry point for the P.DE.I (Personal Data-driven Exocortex Intelligence) framework.
It is responsible for bootstrapping the AI executive, managing connections to the local inference engine (Ollama),
and exposing the interface (CLI or HTTP Server).

Key Functions:
1. Environment Validation: Checks if the local Ollama instance is reachable.
2. Executive Initialization: Loads the `BuddAI` core with the specified configuration and personality.
3. Mode Handling:
   - CLI Mode: Runs an interactive terminal session.
   - Server Mode: Launches a FastAPI/Uvicorn server for web/API access.
4. Port Management: Automatically finds available ports if the default is busy.

Usage:
    python main.py [--server] [--config <path>] [--port <number>]

Where it fits:
    This script is executed AFTER initialization (via `setup.py`). It is the "brain" process that runs continuously
    to handle user requests, code generation, and memory management.
"""

import sys
import argparse
import logging
import socket
import uvicorn

# Try to load .env file for GITHUB_TOKEN and other secrets
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

def get_tailscale_ip() -> str:
    """Detect Tailscale IP (100.x.y.z) by checking route to MagicDNS."""
    try:
        # 100.100.100.100 is the Tailscale MagicDNS IP. 
        # We use a UDP socket to check the routing table without sending data.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("100.100.100.100", 80))
            ip = s.getsockname()[0]
            if ip.startswith("100."):
                return ip
    except:
        pass
    return None

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

            # Detect Tailscale IP for mobile access
            ts_ip = get_tailscale_ip()
            if ts_ip:
                print(f"🔌 Tailscale Detected: {ts_ip}")
                if not args.public_url:
                    args.public_url = f"http://{ts_ip}:{port}/web"

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