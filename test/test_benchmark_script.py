import unittest
import sys
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    import benchmark_model
except ImportError:
    benchmark_model = None

class TestBenchmarkScript(unittest.TestCase):
    def setUp(self):
        if not benchmark_model:
            self.skipTest("benchmark_model module missing")
            
        self.test_dir = PROJECT_ROOT / "test_sandbox_bench"
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.model_dir = self.test_dir / "dummy_model"
        self.model_dir.mkdir()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_benchmark_flow(self):
        """Test the benchmark loop logic."""
        mock_torch = MagicMock()
        mock_transformers = MagicMock()
        
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
        
        # Mock tokenizer output
        mock_inputs = MagicMock()
        mock_inputs.to.return_value = mock_inputs
        mock_inputs.__getitem__.return_value = [1, 2, 3] # input_ids length 3
        mock_tokenizer.return_value = mock_inputs
        
        # Mock generate output (input + 5 new tokens)
        mock_model.generate.return_value = [[1, 2, 3, 4, 5, 6, 7, 8]] 
        mock_model.device = "cpu"
        
        with patch.dict(sys.modules, {'torch': mock_torch, 'transformers': mock_transformers}):
            # Capture stdout to verify output
            with patch('sys.stdout', new=MagicMock()):
                benchmark_model.benchmark(str(self.model_dir), num_runs=1)
                mock_model.generate.assert_called()

if __name__ == "__main__":
    unittest.main()