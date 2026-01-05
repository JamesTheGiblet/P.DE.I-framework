import unittest
import os
from pathlib import Path

class TestGeneratedArtifacts(unittest.TestCase):
    def test_merged_model_structure(self):
        """Verify the merged model directory contains expected HuggingFace artifacts."""
        # Path matches the default output from your previous command
        model_dir = Path("models/pdei-tinyllama-v1-merged")
        
        if not model_dir.exists():
            self.skipTest("Merged model directory not found (run merge script first)")
            
        required_files = [
            "config.json",
            "generation_config.json",
            "tokenizer_config.json",
            "tokenizer.json",
            "special_tokens_map.json"
        ]
        
        for f in required_files:
            self.assertTrue((model_dir / f).exists(), f"Missing {f}")
            
        # Check for weights (safetensors)
        # It might be sharded or single file
        safetensors = list(model_dir.glob("*.safetensors"))
        self.assertTrue(len(safetensors) > 0, "No .safetensors weight files found")
        
    def test_modelfile_content(self):
        """Verify the generated Modelfile exists and has content."""
        modelfile = Path("Modelfile_custom")
        if not modelfile.exists():
            self.skipTest("Modelfile_custom not found")
            
        with open(modelfile, "r") as f:
            content = f.read()
            
        self.assertIn("FROM tinyllama", content)
        self.assertIn("SYSTEM", content)
        self.assertIn("P.DE.I", content)

if __name__ == "__main__":
    unittest.main()
