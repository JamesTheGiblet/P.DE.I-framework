import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add parent directory to path to allow importing pdei_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from pdei_core.server import app

class TestServerAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    @patch('pdei_core.server.buddai_manager')
    def test_root_endpoint(self, mock_manager):
        """Test the HTML dashboard root endpoint"""
        # Mock the instance returned by get_instance
        mock_instance = MagicMock()
        mock_instance.get_user_status.return_value = "Operational"
        mock_manager.get_instance.return_value = mock_instance
        
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Operational", response.text)

    @patch('pdei_core.server.buddai_manager')
    def test_chat_endpoint(self, mock_manager):
        """Test the chat API endpoint"""
        mock_instance = MagicMock()
        mock_instance.chat.return_value = "Hello from Mock AI"
        mock_instance.last_generated_id = 123
        mock_manager.get_instance.return_value = mock_instance
        
        payload = {"message": "Hello", "model": "fast", "forge_mode": "2"}
        response = self.client.post("/api/chat", json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["response"], "Hello from Mock AI")
        self.assertEqual(data["message_id"], 123)
        
        # Verify arguments passed to chat
        mock_instance.chat.assert_called_with("Hello", force_model="fast", forge_mode="2")

    @patch('pdei_core.server.buddai_manager')
    def test_session_history(self, mock_manager):
        """Test retrieving session history"""
        mock_instance = MagicMock()
        mock_instance.context_messages = [{"role": "user", "content": "hi"}]
        mock_manager.get_instance.return_value = mock_instance
        
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["history"]), 1)
        self.assertEqual(data["history"][0]["content"], "hi")

    def test_system_status(self):
        """Test system status endpoint (mocking psutil if needed)"""
        with patch('pdei_core.server.psutil') as mock_psutil:
            if mock_psutil:
                mock_psutil.virtual_memory.return_value.percent = 50.0
                mock_psutil.cpu_percent.return_value = 10.0
            
            response = self.client.get("/api/system/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("cpu", data)
            self.assertIn("memory", data)

if __name__ == '__main__':
    unittest.main()