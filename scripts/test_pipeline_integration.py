import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import convert_to_ollama

class TestPipelineIntegration(unittest.TestCase):
    
    @patch("convert_to_ollama.merge_adapter")
    @patch("subprocess.check_call")
    def test_full_merge_and_create_flow(self, mock_subprocess, mock_merge):
        """
        Verifies that convert_to_ollama correctly orchestrates the merge 
        and then prepares the Ollama creation command.
        """
        # Setup Mocks
        mock_merge.merge_model.return_value = True
        
        # Arguments simulating the user's workflow
        args = MagicMock()
        args.role = None
        args.name = "pdei-test-v1"
        args.base = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" # HF ID for merging
        args.ollama_base = "tinyllama"                   # Ollama tag for Modelfile
        args.adapter = "data/models/adapter_v1"
        args.merge = True
        args.skip_create = False
        
        # Run
        convert_to_ollama.convert(args)
        
        # 1. Verify Merge Call
        # Should use the HF ID (args.base) and adapter path
        mock_merge.merge_model.assert_called_once()
        call_args = mock_merge.merge_model.call_args
        self.assertEqual(call_args[0][0], "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        self.assertEqual(call_args[0][1], "data/models/adapter_v1")
        self.assertIn("pdei-test-v1-merged", call_args[0][2])
        
        # 2. Verify Modelfile Content
        # Should use the Ollama Base (tinyllama)
        with open("Modelfile_custom", "r") as f:
            content = f.read()
            self.assertIn("FROM tinyllama", content)
            
        # 3. Verify Ollama Creation
        mock_subprocess.assert_called_with(["ollama", "create", "pdei-test-v1", "-f", "Modelfile_custom"])
        
        # Cleanup
        if os.path.exists("Modelfile_custom"):
            os.remove("Modelfile_custom")

if __name__ == "__main__":
    unittest.main()