r"""
C:\Users\gilbe\Documents\GitHub\readme-hub\P.DE.I-framework\pdei_core\shared.py
P.DE.I Framework - Shared Configuration & Constants
===================================================

This module contains global constants, configuration paths, and shared utility objects 
(like the Ollama connection pool) used across the framework.

Key Components:
1. Paths: Definitions for DATA_DIR, DB_PATH.
2. Configuration: OLLAMA_HOST, MODELS, APP_NAME.
3. Shared Objects: OLLAMA_POOL for connection reuse.
4. Domain Patterns: Regex patterns for hardware/module detection.

Where it fits:
    Imported by almost all other modules (`main.py`, `buddai_executive.py`, `server.py`) 
    to ensure consistent configuration and avoid circular imports.
"""
import os
import sqlite3
from pathlib import Path
import queue
import http.client

# Global Config
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "conversations.db"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))

# White Label Configuration
APP_NAME = os.getenv("APP_NAME", "AI Executive")
DEFAULT_USER = os.getenv("DEFAULT_USER", "User")
DEFAULT_AI = os.getenv("DEFAULT_AI", "System")

# Shared Models
MODELS = {
    "fast": "qwen2.5-coder:1.5b",
    "balanced": "qwen2.5-coder:3b"
}

# Shared Connection Pool logic to avoid "port in use" or "too many connections" errors
class OllamaConnectionPool:
    def __init__(self, host, port, max_size=10):
        self.host = host
        self.port = port
        self.pool = queue.Queue(maxsize=max_size)
    def get_connection(self):
        try: return self.pool.get_nowait()
        except: return http.client.HTTPConnection(self.host, self.port, timeout=90)
    def return_connection(self, conn):
        try: self.pool.put_nowait(conn)
        except: conn.close()

OLLAMA_POOL = OllamaConnectionPool(OLLAMA_HOST, OLLAMA_PORT)

# Server Availability Check
try:
    import fastapi
    import uvicorn
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False

# Shared Patterns
COMPLEX_TRIGGERS = [
    "multiple modules", "integrate", "combine", "modular", "state machine", "safety", "failsafe", "logic", "protocol", "integration",
    "complete system", "controller", "full stack"
]
MODULE_PATTERNS = {
    "ble": ["ble", "bluetooth", "phone app", "remote"],
    "servo": ["servo", "flipper", "arm", "mg996", "sg90"],
    "motor": ["motor", "drive", "l298n", "movement", "wheels"],
    "safety": ["safety", "timeout", "failsafe", "emergency"],
    "battery": ["battery", "voltage", "power"],
    "sensor": ["sensor", "distance", "proximity", "ultrasonic", "ir", "ldr", "light", "photocell"],
    "weapon": ["weapon", "combat", "arming", "fire", "spinner", "flipper"],
    "logic": ["state machine", "logic", "structure", "flow", "armed", "disarmed"],
    "led": ["led", "light", "brightness", "indicator"]
}