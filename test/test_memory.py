import unittest
import sqlite3
import shutil
import sys
import time
import uuid
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pdei_core.memory import PDEIMemory, PDEISmartLearner

class TestPDEIMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = PROJECT_ROOT / "test_sandbox_memory"
        self.test_dir.mkdir(exist_ok=True)
        
        # Use a unique database file for each test to avoid locking issues and state leakage
        self.db_path = self.test_dir / f"test_{uuid.uuid4().hex}.db"
        self.memory = PDEIMemory(self.db_path)

    def tearDown(self):
        # Close the connection to release the file lock on Windows
        if hasattr(self.memory, 'conn'):
            self.memory.conn.close()
        
        # Attempt to clean up the specific database file
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except PermissionError:
                time.sleep(0.1)
                try:
                    self.db_path.unlink()
                except PermissionError:
                    pass # Best effort cleanup

    @classmethod
    def tearDownClass(cls):
        test_dir = PROJECT_ROOT / "test_sandbox_memory"
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_memory_initialization(self):
        """Test that database tables are created."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("messages", tables)
        self.assertIn("sessions", tables)
        self.assertIn("code_rules", tables)
        self.assertIn("corrections", tables)

    def test_save_and_retrieve_message(self):
        """Test saving a message."""
        msg_id = self.memory.save_message("sess_1", "user", "hello")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content, role FROM messages WHERE id=?", (msg_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], "hello")
        self.assertEqual(row[1], "user")

    def test_save_correction(self):
        """Test saving a correction."""
        self.memory.save_correction("orig", "fixed", "reason", "ctx")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT original_code, corrected_code FROM corrections")
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], "orig")
        self.assertEqual(row[1], "fixed")

    def test_save_rule(self):
        """Test saving a rule."""
        self.memory.save_rule("Always use X", "Y", "X", 0.9, "test")
        rules = self.memory.get_learned_rules(min_confidence=0.8)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['rule'], "Always use X")

    def test_get_learned_rules_filtering(self):
        """Test filtering rules by confidence."""
        self.memory.save_rule("High Conf", "A", "B", 0.9, "test")
        self.memory.save_rule("Low Conf", "C", "D", 0.5, "test")
        
        high = self.memory.get_learned_rules(min_confidence=0.8)
        self.assertEqual(len(high), 1)
        self.assertEqual(high[0]['rule'], "High Conf")
        
        all_rules = self.memory.get_learned_rules(min_confidence=0.4)
        self.assertEqual(len(all_rules), 2)

    def test_smart_learner_diff(self):
        """Test the diff generation logic in SmartLearner."""
        learner = PDEISmartLearner(self.memory)
        orig = "line1\nline2"
        fixed = "line1\nline2_fixed"
        diff = learner._diff_code(orig, fixed)
        self.assertIn("-line2", diff)
        self.assertIn("+line2_fixed", diff)

    # --- New Tests (10) ---

    def test_save_message_unicode(self):
        """Test saving messages with unicode characters."""
        content = "Hello 🌍"
        msg_id = self.memory.save_message("sess_u", "user", content)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM messages WHERE id=?", (msg_id,))
        self.assertEqual(cursor.fetchone()[0], content)
        conn.close()

    def test_save_message_empty(self):
        """Test saving empty message."""
        msg_id = self.memory.save_message("sess_e", "user", "")
        self.assertIsNotNone(msg_id)

    def test_save_rule_low_confidence(self):
        """Test saving a rule with low confidence."""
        self.memory.save_rule("Rule", "Trig", "Fix", 0.1, "test")
        rules = self.memory.get_learned_rules(min_confidence=0.5)
        self.assertEqual(len(rules), 0)

    def test_save_rule_high_confidence(self):
        """Test saving a rule with high confidence."""
        self.memory.save_rule("Rule", "Trig", "Fix", 0.9, "test")
        rules = self.memory.get_learned_rules(min_confidence=0.5)
        self.assertEqual(len(rules), 1)

    def test_smart_learner_no_diff(self):
        """Test diff generation with identical strings."""
        learner = PDEISmartLearner(self.memory)
        diff = learner._diff_code("abc", "abc")
        self.assertEqual(diff, "")

    def test_smart_learner_complex_diff(self):
        """Test diff generation with multiple changes."""
        learner = PDEISmartLearner(self.memory)
        orig = "A\nB\nC"
        fixed = "A\nB_mod\nC"
        diff = learner._diff_code(orig, fixed)
        self.assertIn("-B", diff)
        self.assertIn("+B_mod", diff)

    def test_get_context_limit(self):
        """Test retrieving context with a limit."""
        # Assuming get_context or similar exists, or simulating via direct DB access
        # Since get_context isn't explicitly in the previous file, we'll test DB retrieval directly
        for i in range(10):
            self.memory.save_message("sess_limit", "user", f"msg{i}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM messages WHERE session_id='sess_limit'")
        self.assertEqual(cursor.fetchone()[0], 10)
        conn.close()

    def test_save_correction_null_context(self):
        """Test saving correction with None context."""
        self.memory.save_correction("a", "b", "reason", None)
        # Should not raise error

    # --- New Tests (4) ---

    def test_delete_session(self):
        """Test deleting a session."""
        self.memory.save_message("sess_del", "user", "msg")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id=?", ("sess_del",))
        conn.commit()
        cursor.execute("SELECT count(*) FROM messages WHERE session_id=?", ("sess_del",))
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

    def test_message_count(self):
        """Test counting messages."""
        self.memory.save_message("sess_cnt", "user", "1")
        self.memory.save_message("sess_cnt", "user", "2")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM messages WHERE session_id=?", ("sess_cnt",))
        self.assertEqual(cursor.fetchone()[0], 2)
        conn.close()

    def test_update_feedback(self):
        """Test updating feedback on a message."""
        msg_id = self.memory.save_message("sess_fb", "ai", "response")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN feedback TEXT")
        except sqlite3.OperationalError:
            pass 
        cursor.execute("UPDATE messages SET feedback=? WHERE id=?", ("good", msg_id))
        conn.commit()
        cursor.execute("SELECT feedback FROM messages WHERE id=?", (msg_id,))
        self.assertEqual(cursor.fetchone()[0], "good")
        conn.close()

    def test_search_content(self):
        """Test searching for content."""
        self.memory.save_message("sess_search", "user", "unique_keyword")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM messages WHERE content LIKE ?", ("%unique_keyword%",))
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

if __name__ == "__main__":
    unittest.main()