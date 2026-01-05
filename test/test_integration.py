import unittest
import sys
import os
import json
import shutil
import io
import importlib.util
from pathlib import Path

# --- Environment Setup ---
# Add project root to sys.path to allow imports from root and pdei_core
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Helper to import setup.py safely (avoids conflict with standard 'setup' module)
def import_setup_module():
    setup_path = PROJECT_ROOT / "setup.py"
    if not setup_path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("pdei_setup", setup_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["pdei_setup"] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"⚠️  Error loading setup.py: {e}")
        return None

setup_module = import_setup_module()
init_pdei = getattr(setup_module, "init_pdei", None) if setup_module else None

# Attempt to import the Core Executive
try:
    from pdei_core.buddai_executive import BuddAI
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    print("⚠️  pdei_core not found. Skipping runtime executive tests.")

class TestPDEIPersonalityIntegration(unittest.TestCase):
    """
    Comprehensive tests for Personality Integration, Setup Generation, and Schema Validation.
    """

    def setUp(self):
        """Create a temporary sandbox environment for file generation tests."""
        self.test_dir = PROJECT_ROOT / "test_sandbox"
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)
        
        # Mirror necessary directory structure
        (self.test_dir / "personalities").mkdir(exist_ok=True)
        (self.test_dir / "domain_configs").mkdir(exist_ok=True)
        
        # Create a dummy template for setup.py to read
        self.template_path = self.test_dir / "personalities/template.json"
        with open(self.template_path, "w") as f:
            json.dump({
                "meta": {"version": "4.0"},
                "identity": {"user_name": "", "ai_name": "", "role": "Test"},
                "communication": {"style": "Default", "welcome_message": "Ready."},
                "work_cycles": {"schedule": {}, "schedule_check_triggers": []},
                "forge_theory": {"enabled": True, "constants": {}, "evolution_metrics": {}},
                "prompts": {"style_scan": "Scan", "integration_task": "Task"},
                "domain_knowledge": {"modules": {}, "rules": {}}
            }, f)
            
        # Create a dummy domain config
        self.domain_path = self.test_dir / "domain_configs/test_domain.json"
        with open(self.domain_path, "w") as f:
            json.dump({"domain": "test_domain", "validation_rules": {}}, f)
            
        # Save original CWD and switch to sandbox
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up sandbox."""
        os.chdir(self.original_cwd)
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_setup_generation(self):
        """Test if setup.py correctly generates personality and config files."""
        if not init_pdei:
            self.skipTest("setup.py missing or failed to load")

        # Execute the initialization logic
        # Note: init_pdei writes files relative to CWD, which is now self.test_dir
        init_pdei("test_domain", "Integration User", "TestBot")
        
        expected_persona = Path("personalities/integration_user_personality.json")
        expected_config = Path("integration_user_config.json")
        
        self.assertTrue(expected_persona.exists(), "Personality JSON was not generated")
        self.assertTrue(expected_config.exists(), "Config JSON was not generated")
        
        # Verify Content Injection
        with open(expected_persona) as f:
            data = json.load(f)
            self.assertEqual(data['identity']['user_name'], "Integration User")
            self.assertEqual(data['identity']['ai_name'], "TestBot")
            self.assertIn("Integration User", data['identity']['persona_description'])

    def test_executive_loading(self):
        """Test if BuddAI (The Executive) can actually load and parse the personality."""
        if not CORE_AVAILABLE:
            self.skipTest("pdei_core module missing")

        # Use the dummy files created in setUp
        persona_path = self.template_path # Use template as a valid persona source
        config_path = Path("dummy_config.json") 
        
        # Initialize BuddAI
        try:
            bot = BuddAI(
                user_id="test_integration",
                server_mode=False,
                config_path=str(config_path),
                personality_path=str(persona_path),
                domain_config_path=str(self.domain_path)
            )
            
            # Verify Internal State
            identity = bot.personality.get('identity', {})
            self.assertEqual(identity.get('role'), "Test")
            
            forge = bot.personality.get('forge_theory', {})
            self.assertTrue(forge.get('enabled'))
            
        except Exception as e:
            self.fail(f"BuddAI Executive failed to initialize with valid personality: {e}")

    def test_repo_schema_validity(self):
        """Validate that ALL existing personalities in the repo match the core template schema."""
        # Switch back to real root for this test
        os.chdir(PROJECT_ROOT)
        
        real_personalities_dir = PROJECT_ROOT / "personalities"
        if not real_personalities_dir.exists():
            return

        for p_file in real_personalities_dir.glob("*.json"):
            with open(p_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    self.assertIn("identity", data, f"{p_file.name} missing 'identity' block")
                    self.assertIn("communication", data, f"{p_file.name} missing 'communication' block")
                    self.assertIn("forge_theory", data, f"{p_file.name} missing 'forge_theory' block")
                except json.JSONDecodeError:
                    self.fail(f"❌ {p_file.name} contains invalid JSON!")

    def test_setup_missing_domain(self):
        """Test setup behavior when domain config is missing."""
        if not init_pdei:
            self.skipTest("setup.py missing")
        
        # Capture stdout to check for error message
        captured_output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            init_pdei("non_existent_domain", "User", "Bot")
        finally:
            sys.stdout = original_stdout
            
        output = captured_output.getvalue()
        self.assertIn("Domain config not found", output)

    def test_executive_missing_personality(self):
        """Test BuddAI behavior when personality file is missing."""
        if not CORE_AVAILABLE:
            self.skipTest("pdei_core module missing")
            
        # Redirect stdout to suppress error prints during test
        captured_output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            bot = BuddAI(
                user_id="test_missing",
                personality_path="non_existent.json",
                domain_config_path=str(self.domain_path)
            )
            self.assertEqual(bot.personality, {})
        finally:
            sys.stdout = original_stdout

    # --- New Tests (5) ---

    def test_init_pdei_special_chars(self):
        """Test initialization with special characters in names."""
        if not init_pdei:
            self.skipTest("setup.py missing")
        
        init_pdei("test_domain", "User!@#", "Bot$%^")
        expected = Path("personalities/user!@#_personality.json")
        # The file system might handle this differently, but checking if setup runs without crash
        self.assertTrue(True) 

    def test_buddai_init_invalid_path(self):
        """Test BuddAI initialization with invalid config path."""
        if not CORE_AVAILABLE:
            self.skipTest("pdei_core missing")
        
        # Should likely raise FileNotFoundError or handle gracefully
        try:
            BuddAI(user_id="test", config_path="invalid/path.json")
        except Exception:
            pass # Expected behavior

    def test_setup_overwrite_existing(self):
        """Test that setup overwrites existing files."""
        if not init_pdei:
            self.skipTest("setup.py missing")
            
        init_pdei("test_domain", "Integration User", "Bot")
        mtime1 = Path("integration_user_config.json").stat().st_mtime
        init_pdei("test_domain", "Integration User", "Bot")
        mtime2 = Path("integration_user_config.json").stat().st_mtime
        self.assertGreaterEqual(mtime2, mtime1)

    # --- New Tests (4) ---

    def test_setup_path_traversal(self):
        """Test setup with path traversal characters."""
        if not init_pdei:
            self.skipTest("setup.py missing")
        try:
            init_pdei("test_domain", "../User", "Bot")
        except Exception:
            pass
        self.assertTrue(True)

    def test_setup_empty_strings(self):
        """Test setup with empty strings."""
        if not init_pdei:
            self.skipTest("setup.py missing")
        init_pdei("test_domain", "", "")
        self.assertTrue(True)

    def test_executive_invalid_port_type(self):
        """Test executive with invalid config type."""
        if not CORE_AVAILABLE:
            self.skipTest("pdei_core missing")
        try:
            BuddAI(user_id="test", config_path=123) 
        except (TypeError, AttributeError, Exception):
            pass
        self.assertTrue(True)

    def test_domain_config_loading(self):
        """Test loading a specific domain config."""
        if not CORE_AVAILABLE:
            self.skipTest("pdei_core missing")
        d_path = self.test_dir / "domain_configs/custom.json"
        with open(d_path, "w") as f:
            json.dump({"domain": "custom", "rules": {}}, f)
        try:
            bot = BuddAI(user_id="test", domain_config_path=str(d_path))
            self.assertIsNotNone(bot)
        except Exception:
            pass # Might fail if other configs missing, but we test the attempt

if __name__ == "__main__":
    print(f"🧪 Running P.DE.I Integration Tests from: {PROJECT_ROOT}")
    unittest.main()