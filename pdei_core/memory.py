import sqlite3
import re
import difflib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union

class PDEIMemory:
    """
    P.DE.I Framework Core Memory
    
    Handles database interactions, session management, and learning persistence.
    Acts as the central storage unit for the Exocortex.
    """
    def __init__(self, db_path: Union[str, Path], user_id: str = "default"):
        self.db_path = Path(db_path)
        self.user_id = user_id
        self.ensure_db_init()
        
        # Sub-components
        self.shadow_engine = PDEIShadowEngine(self)
        self.adaptive_learner = PDEIAdaptiveLearner(self)
        self.smart_learner = PDEISmartLearner(self)

    def get_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        return sqlite3.connect(self.db_path)

    def ensure_db_init(self):
        """Initialize the generic schema if tables don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Core tables definition
        tables = [
            """CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                title TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS repo_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                file_path TEXT,
                repo_name TEXT,
                function_name TEXT,
                content TEXT,
                last_modified TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS style_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                category TEXT,
                preference TEXT,
                confidence FLOAT,
                extracted_at TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                positive BOOLEAN,
                comment TEXT,
                timestamp TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                original_code TEXT,
                corrected_code TEXT,
                reason TEXT,
                context TEXT,
                processed BOOLEAN DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS code_rules (
                id INTEGER PRIMARY KEY,
                rule_text TEXT,
                pattern_find TEXT,
                pattern_replace TEXT,
                context TEXT,
                confidence FLOAT,
                learned_from TEXT,
                times_applied INTEGER DEFAULT 0
            )"""
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
            
        conn.commit()
        conn.close()

    # --- Generic DB Helpers ---
    
    def save_message(self, session_id: str, role: str, content: str) -> int:
        """Log a chat message."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.now().isoformat())
        )
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return msg_id

    def save_correction(self, original: str, corrected: str, reason: str, context: str):
        """Log a user correction for learning."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO corrections 
            (timestamp, original_code, corrected_code, reason, context)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), original, corrected, reason, context))
        conn.commit()
        conn.close()

    def get_learned_rules(self, min_confidence: float = 0.8) -> List[Dict]:
        """Retrieve high-confidence rules."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rule_text, pattern_find, pattern_replace, confidence FROM code_rules WHERE confidence >= ?", (min_confidence,))
        rows = cursor.fetchall()
        conn.close()
        return [{"rule": r[0], "find": r[1], "replace": r[2], "confidence": r[3]} for r in rows]

    def save_rule(self, rule_text: str, find: str, replace: str, confidence: float, source: str):
        """Persist a learned rule."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO code_rules 
            (rule_text, pattern_find, pattern_replace, confidence, learned_from)
            VALUES (?, ?, ?, ?, ?)
        """, (rule_text, find, replace, confidence, source))
        conn.commit()
        conn.close()


class PDEIShadowEngine:
    """
    Generic Shadow Suggestion Engine.
    Proactively suggests modules/settings based on user/project history.
    """
    def __init__(self, memory: PDEIMemory):
        self.memory = memory

    def get_suggestions(self, user_input: str, context: Dict[str, Any] = None) -> List[str]:
        """
        Generate proactive suggestions.
        In a full implementation, this would query the repo_index for correlations.
        """
        # Placeholder for generic suggestion logic
        # This would typically check for companion modules (e.g. "If using X, usually use Y")
        return []

    def get_all_suggestions(self, user_input: str, response: str) -> List[str]:
        """Wrapper to get suggestions based on conversation context."""
        return self.get_suggestions(user_input, {"response": response})


class PDEIAdaptiveLearner:
    """
    Generic Adaptive Learner.
    Analyzes session history to identify implicit preferences and corrections.
    """
    def __init__(self, memory: PDEIMemory):
        self.memory = memory

    def learn_from_session(self, session_id: str):
        """Analyze what worked/failed in a session."""
        conn = self.memory.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, role, content 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY id ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        conn.close()
        
        # Logic to detect "No, that's wrong" or "Better" patterns would go here
        # and call self.memory.save_rule()
        pass


class PDEISmartLearner:
    """
    Generic Pattern Extractor.
    Extracts explicit rules from user corrections.
    """
    def __init__(self, memory: PDEIMemory):
        self.memory = memory

    def analyze_corrections(self, ai_interface=None) -> List[Dict]:
        """Find common patterns in fixes."""
        conn = self.memory.get_connection()
        cursor = conn.cursor()
        
        # Fetch unprocessed corrections
        cursor.execute("""
            SELECT id, original_code, corrected_code, reason 
            FROM corrections
            WHERE processed IS NOT 1
            LIMIT 5
        """)
        
        corrections = cursor.fetchall()
        patterns = []
        
        for row_id, original, corrected, reason in corrections:
            if corrected and original:
                # 1. Diff Analysis
                diff = self._diff_code(original, corrected)
                
                # 2. LLM Extraction (if interface provided)
                # This is where we'd ask the LLM to extract a rule from the diff/reason
                
            # Mark as processed
            cursor.execute("UPDATE corrections SET processed = 1 WHERE id = ?", (row_id,))
            conn.commit()
            
        conn.close()
        return patterns

    def _diff_code(self, original: str, corrected: str) -> str:
        """Generate a unified diff."""
        return "\n".join(difflib.unified_diff(
            original.splitlines(), 
            corrected.splitlines(), 
            fromfile='original', 
            tofile='corrected', 
            lineterm=''
        ))