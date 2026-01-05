import unittest
import sys
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Add scripts directory to sys.path
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    import merge_adapter
except ImportError:
    print("⚠️  Could not import merge_adapter.py. Ensure it is in the scripts directory.")
    merge_adapter = None

class TestMergeAdapterScript(unittest.TestCase):
    def setUp(self):
        if not merge_adapter:
            self.skipTest("merge_adapter module missing")
            
        self.test_dir = PROJECT_ROOT / "test_sandbox_merge"
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)
        
        self.adapter_dir = self.test_dir / "adapter"
        self.adapter_dir.mkdir()
        self.output_dir = self.test_dir / "merged_model"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_merge_missing_deps(self):
        """Test graceful failure when ML libs are missing."""
        # Simulate missing torch
        with patch.dict(sys.modules, {'torch': None}):
            result = merge_adapter.merge_model("base", str(self.adapter_dir), str(self.output_dir))
            self.assertFalse(result)

    def test_merge_success_flow(self):
        """Test the merge flow with mocked libraries."""
        mock_torch = MagicMock()
        mock_transformers = MagicMock()
        mock_peft = MagicMock()
        
        # Setup mocks for the chain of calls
        mock_base_model = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_base_model
        mock_transformers.AutoTokenizer.from_pretrained.return_value = MagicMock()
        
        mock_peft_model = MagicMock()
        mock_peft.PeftModel.from_pretrained.return_value = mock_peft_model
        
        mock_merged_model = MagicMock()
        mock_peft_model.merge_and_unload.return_value = mock_merged_model
        # Mock device type for CPU check
        mock_merged_model.device.type = 'cpu'
        mock_merged_model.half.return_value = mock_merged_model
        
        modules = {
            'torch': mock_torch,
            'transformers': mock_transformers,
            'peft': mock_peft
        }
        
        with patch.dict(sys.modules, modules):
            result = merge_adapter.merge_model("base", str(self.adapter_dir), str(self.output_dir))
            
            self.assertTrue(result)
            mock_transformers.AutoModelForCausalLM.from_pretrained.assert_called()
            mock_peft.PeftModel.from_pretrained.assert_called_with(mock_base_model, str(self.adapter_dir))
            mock_peft_model.merge_and_unload.assert_called()
            mock_merged_model.save_pretrained.assert_called_with(str(self.output_dir), safe_serialization=True, max_shard_size="1GB")
            mock_merged_model.half.assert_called_once()

    def test_script_subprocess_help(self):
        """Verify script runs via CLI and prints help."""
        script_path = SCRIPTS_DIR / "merge_adapter.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

if __name__ == "__main__":
    unittest.main()