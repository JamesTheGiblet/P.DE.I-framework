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
        self.client = TestClient(app, raise_server_exceptions=False)
        
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

    @patch('pdei_core.server.buddai_manager')
    def test_new_session_endpoint(self, mock_manager):
        """Test creating a new session"""
        mock_instance = MagicMock()
        mock_instance.start_new_session.return_value = "new_session_123"
        mock_manager.get_instance.return_value = mock_instance
        
        response = self.client.post("/api/session/new")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["session_id"], "new_session_123")

    @patch('pdei_core.server.buddai_manager')
    def test_clear_session_endpoint(self, mock_manager):
        """Test clearing the current session"""
        mock_instance = MagicMock()
        mock_manager.get_instance.return_value = mock_instance
        
        response = self.client.post("/api/session/clear")
        self.assertEqual(response.status_code, 200)
        mock_instance.clear_current_session.assert_called_once()

    @patch('pdei_core.server.buddai_manager')
    def test_feedback_endpoint(self, mock_manager):
        """Test submitting feedback"""
        mock_instance = MagicMock()
        mock_instance.record_feedback.return_value = None
        mock_manager.get_instance.return_value = mock_instance
        
        payload = {"message_id": 1, "positive": True, "comment": "Good job"}
        response = self.client.post("/api/feedback", json=payload)
        
        self.assertEqual(response.status_code, 200)
        mock_instance.record_feedback.assert_called_with(1, True, "Good job")

    # --- New Tests (10) ---

    def test_chat_missing_message(self):
        """Test chat endpoint with missing message field."""
        response = self.client.post("/api/chat", json={"model": "fast"})
        self.assertEqual(response.status_code, 422) # Validation Error

    def test_chat_empty_body(self):
        """Test chat endpoint with empty body."""
        response = self.client.post("/api/chat", json={})
        self.assertEqual(response.status_code, 422)

    def test_feedback_missing_id(self):
        """Test feedback with missing message_id."""
        response = self.client.post("/api/feedback", json={"positive": True})
        self.assertEqual(response.status_code, 422)

    def test_feedback_invalid_types(self):
        """Test feedback with invalid data types."""
        response = self.client.post("/api/feedback", json={"message_id": "abc", "positive": "yes"})
        self.assertEqual(response.status_code, 422)

    def test_method_not_allowed_get_chat(self):
        """Test GET on POST-only chat endpoint."""
        response = self.client.get("/api/chat")
        self.assertEqual(response.status_code, 405)

    def test_method_not_allowed_post_history(self):
        """Test POST on GET-only history endpoint."""
        response = self.client.post("/api/history")
        self.assertEqual(response.status_code, 405)

    def test_404_unknown_endpoint(self):
        """Test accessing a non-existent endpoint."""
        response = self.client.get("/api/does_not_exist")
        self.assertEqual(response.status_code, 404)

    @patch('pdei_core.server.buddai_manager')
    def test_chat_internal_error(self, mock_manager):
        """Test handling of internal server errors during chat."""
        mock_instance = MagicMock()
        mock_instance.chat.side_effect = Exception("Internal Fail")
        mock_manager.get_instance.return_value = mock_instance
        
        response = self.client.post("/api/chat", json={"message": "hi"})
        # FastAPI default exception handler usually returns 500
        self.assertEqual(response.status_code, 500)

    # --- New Tests (5) ---

    def test_root_head_request(self):
        """Test HEAD request on root."""
        response = self.client.head("/")
        self.assertEqual(response.status_code, 405)

    def test_chat_large_payload(self):
        """Test chat with large payload."""
        large_msg = "A" * 10000
        with patch('pdei_core.server.buddai_manager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.chat.return_value = "Response"
            mock_manager.get_instance.return_value = mock_instance
            response = self.client.post("/api/chat", json={"message": large_msg})
            self.assertEqual(response.status_code, 200)

    def test_chat_invalid_model_handling(self):
        """Test chat with unknown model."""
        with patch('pdei_core.server.buddai_manager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.chat.return_value = "Fallback Response"
            mock_manager.get_instance.return_value = mock_instance
            response = self.client.post("/api/chat", json={"message": "hi", "model": "unknown_model"})
            self.assertEqual(response.status_code, 200)
            mock_instance.chat.assert_called_with("hi", force_model="unknown_model", forge_mode='2')

    def test_cors_preflight(self):
        """Test CORS preflight request."""
        response = self.client.options("/api/chat", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        self.assertTrue(response.status_code in [200, 204])

    def test_server_headers(self):
        """Test presence of standard headers."""
        response = self.client.get("/")
        self.assertIn("content-type", response.headers)

if __name__ == '__main__':
    unittest.main()