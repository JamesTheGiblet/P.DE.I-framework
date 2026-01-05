import unittest
import sys
import os
import sqlite3
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Add scripts directory to sys.path to allow importing retrain_model
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

retrain_model_path = SCRIPTS_DIR / "retrain_model.py"
if retrain_model_path.exists():
    try:
        import retrain_model
    except ImportError as e:
        print(f"⚠️  Could not import retrain_model.py due to ImportError: {e}")
        retrain_model = None
else:
    print(f"⚠️  retrain_model.py not found in {SCRIPTS_DIR}. Please ensure the file exists.")
    retrain_model = None

class TestRetrainModelScript(unittest.TestCase):
    def setUp(self):
        if not retrain_model:
            self.skipTest("retrain_model module missing")

        self.test_dir = PROJECT_ROOT / "test_sandbox_retrain"
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)
        
        self.db_path = self.test_dir / "memory.db"
        self.output_dir = self.test_dir / "adapter_output"
        
        # Create dummy DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE corrections (
                id INTEGER PRIMARY KEY,
                original_code TEXT,
                corrected_code TEXT,
                context TEXT
            )
        """)
        # Insert dummy data
        cursor.execute("INSERT INTO corrections (original_code, corrected_code, context) VALUES (?, ?, ?)",
                       ("bad_code", "good_code", "test_ctx"))
        conn.commit()
        conn.close()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_load_training_data(self):
        """Test data loading from DB."""
        data = retrain_model.load_training_data(str(self.db_path))
        self.assertEqual(len(data), 1)
        self.assertIn("bad_code", data[0]['prompt'])
        self.assertIn("good_code", data[0]['completion'])

    def test_train_model_missing_deps(self):
        """Test train_model handles missing dependencies gracefully."""
        # Force import error for 'torch' to simulate missing deps
        with patch.dict(sys.modules, {'torch': None}):
            # We need to reload or ensure the function re-imports. 
            # retrain_model.train_model has imports inside the function, so this works.
            result = retrain_model.train_model([], output_dir=str(self.output_dir))
            self.assertFalse(result)

    def test_train_model_success_flow(self):
        """Test the training flow when dependencies exist (mocked)."""
        # Mock all the heavy ML libraries
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True # Simulate GPU present
        mock_torch.float16 = "float16"
        
        mock_datasets = MagicMock()
        mock_dataset_obj = MagicMock()
        mock_datasets.Dataset.from_list.return_value = mock_dataset_obj
        mock_dataset_obj.map.return_value = mock_dataset_obj # Support chaining .map()
        
        mock_peft = MagicMock()
        mock_transformers = MagicMock()
        mock_trl = MagicMock()
        
        # Setup specific return values needed for the flow
        mock_transformers.AutoTokenizer.from_pretrained.return_value = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = MagicMock()
        mock_peft.get_peft_model.return_value = MagicMock()
        
        mock_trainer_instance = MagicMock()
        mock_trl.SFTTrainer.return_value = mock_trainer_instance
        
        modules = {
            'torch': mock_torch,
            'datasets': mock_datasets,
            'peft': mock_peft,
            'transformers': mock_transformers,
            'trl': mock_trl
        }
        
        with patch.dict(sys.modules, modules):
            data = [{"prompt": "p", "completion": "c"}]
            result = retrain_model.train_model(data, output_dir=str(self.output_dir))
            
            self.assertTrue(result)
            mock_trl.SFTTrainer.assert_called_once()
            
            # Verify we are using dataset_text_field instead of formatting_func
            _, kwargs = mock_trl.SFTTrainer.call_args
            self.assertNotIn('formatting_func', kwargs)
            
            mock_trainer_instance.train.assert_called_once()
            mock_trainer_instance.model.save_pretrained.assert_called_once_with(str(self.output_dir))

    def test_train_model_cpu_fallback(self):
        """Test training flow on CPU (no GPU detected)."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False # Simulate CPU only
        
        mock_transformers = MagicMock()
        mock_transformers.AutoTokenizer.from_pretrained.return_value = MagicMock()
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = MagicMock()
        
        mock_peft = MagicMock()
        mock_peft.get_peft_model.return_value = MagicMock()
        
        mock_trl = MagicMock()
        mock_trainer = MagicMock()
        mock_trl.SFTTrainer.return_value = mock_trainer

        mock_datasets = MagicMock()
        mock_dataset_obj = MagicMock()
        mock_datasets.Dataset.from_list.return_value = mock_dataset_obj
        mock_dataset_obj.map.return_value = mock_dataset_obj
        
        modules = {
            'torch': mock_torch,
            'datasets': mock_datasets,
            'peft': mock_peft,
            'transformers': mock_transformers,
            'trl': mock_trl
        }
        
        with patch.dict(sys.modules, modules):
            data = [{"prompt": "p", "completion": "c"}]
            result = retrain_model.train_model(data, output_dir=str(self.output_dir))
            
            self.assertTrue(result)
            # Verify FP16 was disabled in TrainingArguments
            args_call = mock_transformers.TrainingArguments.call_args
            self.assertFalse(args_call.kwargs.get('fp16'), "FP16 should be False on CPU")
            self.assertEqual(args_call.kwargs.get('optim'), "adamw_torch", "Optimizer should be adamw_torch on CPU")

    @patch("retrain_model.train_model")
    def test_main_execution(self, mock_train):
        """Test main function argument parsing and flow."""
        mock_train.return_value = True
        
        # Calculate relative path for args because script resolves relative to PROJECT_ROOT
        rel_db_path = os.path.relpath(self.db_path, PROJECT_ROOT)
        rel_out_path = os.path.relpath(self.output_dir, PROJECT_ROOT)
        
        test_args = ["retrain_model.py", "--db", str(rel_db_path), "--output", str(rel_out_path)]
        
        with patch("sys.argv", test_args):
            retrain_model.main()
        
        mock_train.assert_called_once()
        # Verify data passed to train_model has 1 item
        call_args = mock_train.call_args
        self.assertEqual(len(call_args[0][0]), 1)

    def test_script_subprocess_help(self):
        """Verify the script is executable via CLI and prints help without crashing."""
        script_path = SCRIPTS_DIR / "retrain_model.py"
        
        # Execute the script in a separate process to ensure no syntax/import errors at runtime
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, f"Script crashed: {result.stderr}")
        self.assertIn("usage:", result.stdout)

if __name__ == "__main__":
    unittest.main()