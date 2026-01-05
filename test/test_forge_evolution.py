import unittest
import json
import sys
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Import the actual logic
from pdei_core.evolution import check_evolution_trigger, evolution_watchdog

class TestForgeTheoryEvolution(unittest.IsolatedAsyncioTestCase):
    """
    Tests the evolutionary logic of the Forge Theory module.
    Simulates the 'watchdog' process found in main.py.
    """

    def setUp(self):
        # Define a standard personality state for testing
        self.personality_state = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {
                    "data_points_collected": 0,
                    "retrain_threshold": 50,
                    "generation": 1
                }
            }
        }

    def test_threshold_trigger(self):
        """Verify evolution triggers when data points meet threshold."""
        metrics = self.personality_state["forge_theory"]["evolution_metrics"]
        metrics["data_points_collected"] = 50  # Meet threshold
        
        triggered = check_evolution_trigger(self.personality_state)
        
        self.assertTrue(triggered, "Watchdog should trigger when threshold is met")
        self.assertEqual(metrics["generation"], 2, "Generation should increment")
        self.assertEqual(metrics["data_points_collected"], 0, "Data points should reset")

    def test_below_threshold(self):
        """Verify evolution does NOT trigger below threshold."""
        metrics = self.personality_state["forge_theory"]["evolution_metrics"]
        metrics["data_points_collected"] = 49
        
        triggered = check_evolution_trigger(self.personality_state)
        
        self.assertFalse(triggered, "Watchdog triggered prematurely")
        self.assertEqual(metrics["generation"], 1)

    def test_disabled_forge(self):
        """Verify evolution is suppressed if Forge Theory is disabled."""
        self.personality_state["forge_theory"]["enabled"] = False
        metrics = self.personality_state["forge_theory"]["evolution_metrics"]
        metrics["data_points_collected"] = 100 # Well above threshold
        
        triggered = check_evolution_trigger(self.personality_state)
        
        self.assertFalse(triggered, "Watchdog triggered while disabled")
        self.assertEqual(metrics["generation"], 1)

    # --- New Tests ---

    def test_missing_forge_theory_key(self):
        """Ensure robust handling when forge_theory key is missing."""
        personality = {}
        triggered = check_evolution_trigger(personality)
        self.assertFalse(triggered)

    def test_missing_metrics_key(self):
        """Ensure robust handling when evolution_metrics key is missing."""
        personality = {"forge_theory": {"enabled": True}}
        triggered = check_evolution_trigger(personality)
        self.assertFalse(triggered)

    def test_default_threshold_behavior(self):
        """Verify default threshold of 100 is used if missing."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 100}
            }
        }
        triggered = check_evolution_trigger(personality)
        self.assertTrue(triggered)
        # Should default generation to 1 then increment to 2
        self.assertEqual(personality["forge_theory"]["evolution_metrics"]["generation"], 2)

    def test_custom_threshold_behavior(self):
        """Verify custom thresholds are respected."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {
                    "data_points_collected": 10,
                    "retrain_threshold": 10
                }
            }
        }
        triggered = check_evolution_trigger(personality)
        self.assertTrue(triggered)

    def test_generation_increment_logic(self):
        """Verify generation increments correctly from existing value."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {
                    "data_points_collected": 50,
                    "retrain_threshold": 50,
                    "generation": 5
                }
            }
        }
        check_evolution_trigger(personality)
        self.assertEqual(personality["forge_theory"]["evolution_metrics"]["generation"], 6)

    def test_data_points_hard_reset(self):
        """Verify data points reset to 0, not just subtracted."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {
                    "data_points_collected": 150, # Way over threshold
                    "retrain_threshold": 50
                }
            }
        }
        check_evolution_trigger(personality)
        self.assertEqual(personality["forge_theory"]["evolution_metrics"]["data_points_collected"], 0)

    @patch("pdei_core.evolution.asyncio.create_subprocess_exec", new_callable=AsyncMock)
    @patch("pdei_core.evolution.Path.exists")
    @patch("pdei_core.evolution.asyncio.sleep")
    async def test_watchdog_script_execution_success(self, mock_sleep, mock_exists, mock_subprocess):
        """Test successful execution of the retraining script."""
        # Break the infinite loop
        mock_sleep.side_effect = asyncio.CancelledError("Break Loop")
        mock_exists.return_value = True
        
        mock_proc = mock_subprocess.return_value
        mock_proc.communicate.return_value = (b"Success", b"")
        mock_proc.returncode = 0
        
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 100, "retrain_threshold": 100}
            }
        }
        mock_buddai = MagicMock()
        mock_buddai.personality = personality
        
        try:
            await evolution_watchdog(lambda: mock_buddai, interval=0)
        except asyncio.CancelledError:
            pass
            
        mock_subprocess.assert_called_once()

    @patch("pdei_core.evolution.asyncio.create_subprocess_exec", new_callable=AsyncMock)
    @patch("pdei_core.evolution.Path.exists")
    @patch("pdei_core.evolution.asyncio.sleep")
    async def test_watchdog_script_execution_failure(self, mock_sleep, mock_exists, mock_subprocess):
        """Test handling of retraining script failure."""
        mock_sleep.side_effect = asyncio.CancelledError("Break Loop")
        mock_exists.return_value = True
        
        mock_proc = mock_subprocess.return_value
        mock_proc.communicate.return_value = (b"", b"Error")
        mock_proc.returncode = 1
        
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 100}
            }
        }
        mock_buddai = MagicMock()
        mock_buddai.personality = personality
        
        try:
            await evolution_watchdog(lambda: mock_buddai, interval=0)
        except asyncio.CancelledError:
            pass
            
        mock_subprocess.assert_called_once()

    @patch("pdei_core.evolution.Path.exists")
    @patch("pdei_core.evolution.asyncio.sleep")
    async def test_watchdog_script_missing(self, mock_sleep, mock_exists):
        """Test behavior when retraining script is missing."""
        mock_sleep.side_effect = asyncio.CancelledError("Break Loop")
        mock_exists.return_value = False
        
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 100}
            }
        }
        mock_buddai = MagicMock()
        mock_buddai.personality = personality
        
        try:
            await evolution_watchdog(lambda: mock_buddai, interval=0)
        except asyncio.CancelledError:
            pass
            
        # Should not crash

    @patch("pdei_core.evolution.asyncio.sleep")
    async def test_watchdog_no_buddai_instance(self, mock_sleep):
        """Test watchdog behavior when provider returns None."""
        mock_sleep.side_effect = asyncio.CancelledError("Break Loop")
        
        try:
            await evolution_watchdog(lambda: None, interval=0)
        except asyncio.CancelledError:
            pass
            
        # Should handle None gracefully and sleep

    # --- New Tests (5) ---

    def test_trigger_exact_threshold(self):
        """Test trigger exactly at threshold."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 10, "retrain_threshold": 10}
            }
        }
        self.assertTrue(check_evolution_trigger(personality))

    def test_trigger_zero_threshold(self):
        """Test trigger with zero threshold (immediate evolution)."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 1, "retrain_threshold": 0}
            }
        }
        self.assertTrue(check_evolution_trigger(personality))

    def test_metrics_update_structure(self):
        """Ensure metrics structure is preserved after update."""
        personality = {
            "forge_theory": {
                "enabled": True,
                "evolution_metrics": {"data_points_collected": 100, "retrain_threshold": 50, "extra": "val"}
            }
        }
        check_evolution_trigger(personality)
        metrics = personality["forge_theory"]["evolution_metrics"]
        self.assertEqual(metrics["extra"], "val")

if __name__ == "__main__":
    print(f"🧬 Running Forge Theory Evolution Tests")
    unittest.main()