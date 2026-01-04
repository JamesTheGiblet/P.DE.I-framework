#!/usr/bin/env python3
"""
C:\Users\gilbe\Documents\GitHub\readme-hub\P.DE.I-framework\pdei_core\buddai_executive.py
P.DE.I Framework - BuddAI Executive Core
========================================

This module defines the `BuddAI` class, which acts as the central "brain" or executive controller
for the P.DE.I framework. It orchestrates the interaction between the user, the LLM (Ollama),
long-term memory (SQLite), and domain-specific validation logic.

Key Responsibilities:
1. Context Management: Maintains session history, user identity, and active hardware profiles.
2. Request Routing: Decides whether a request is a simple chat, a complex modular build, or a database search.
3. Code Generation & Validation: Generates code via LLM and validates it against domain rules (Forge Theory).
4. Learning Loop: Captures user corrections and feedback to refine future outputs.
5. Interface Handling: Supports both CLI interaction and a headless HTTP daemon mode.

Where it fits:
    This is the core logic library imported by `main.py`. While `main.py` handles the entry point and
    process bootstrapping, `buddai_executive.py` contains the actual intelligence and business logic.
"""
import sys, os, json, logging, sqlite3, http.client, http.server, re, zipfile, shutil, queue, socket, argparse, io, threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Union, Generator, Any

try:
    import psutil
except ImportError:
    psutil = None

from pdei_core.logic import PDEIValidator
from pdei_core.memory import PDEIMemory
from pdei_core.shared import DATA_DIR, DB_PATH, MODELS, OLLAMA_HOST, OLLAMA_PORT, COMPLEX_TRIGGERS, SERVER_AVAILABLE, APP_NAME, DEFAULT_USER, DEFAULT_AI, MODULE_PATTERNS

class OllamaConnectionPool:
    def __init__(self, host: str, port: int, max_size: int = 10):
        self.host = host
        self.port = port
        self.pool: queue.Queue = queue.Queue(maxsize=max_size)
        
    def get_connection(self) -> http.client.HTTPConnection:
        try:
            return self.pool.get_nowait()
        except queue.Empty:
            return http.client.HTTPConnection(self.host, self.port, timeout=90)
            
    def return_connection(self, conn: http.client.HTTPConnection):
        try:
            self.pool.put_nowait(conn)
        except queue.Full:
            conn.close()

OLLAMA_POOL = OllamaConnectionPool(OLLAMA_HOST, OLLAMA_PORT)


# --- Shadow Suggestion Engine ---

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_TYPES = [
    "application/zip", "application/x-zip-compressed", "application/octet-stream",
    "text/x-python", "text/plain", "text/x-c++src", "text/x-csrc", "text/javascript", "text/html", "text/css"
]
MAX_UPLOAD_FILES = 20

class PDEIExecutive:
    """
    Base Executive Class for P.DE.I Framework.
    Handles loading of Personality and Domain configurations.
    """
    def __init__(self, personality_path: str, domain_config_path: str):
        self.personality_path = personality_path
        self.domain_config_path = domain_config_path
        
        self.personality = self.load_personality()
        self.domain_config = self.load_domain_config()

    def load_personality(self) -> Dict[str, Any]:
        """Load personality JSON from file."""
        path = Path(self.personality_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading personality: {e}")
        return {}

    def load_domain_config(self) -> Dict[str, Any]:
        """Load domain configuration JSON from file."""
        path = Path(self.domain_config_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading domain config: {e}")
        return {}

    def get_personality_value(self, key_path: str, default: Any = None) -> Any:
        """Retrieve a value from personality using dot notation."""
        return self._get_nested_value(self.personality, key_path, default)

    def get_domain_value(self, key_path: str, default: Any = None) -> Any:
        """Retrieve a value from domain config using dot notation."""
        return self._get_nested_value(self.domain_config, key_path, default)

    def _get_nested_value(self, data: Dict, key_path: str, default: Any) -> Any:
        keys = key_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

class BuddAI(PDEIExecutive):
    """Executive with task breakdown"""

    def is_search_query(self, message: str) -> bool:
        """Check if this is a search query that should query repo_index"""
        message_lower = message.lower()
        search_triggers = [
            "show me", "find", "search for", "list all",
            "what functions", "which repos", "do i have",
            "where did i", "have i used", "examples of",
            "show all", "display"
        ]
        return any(trigger in message_lower for trigger in search_triggers)

    def search_repositories(self, query: str) -> str:
        """Search repo_index for relevant functions and code"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM repo_index WHERE user_id = ?", (self.user_id,))
        count = cursor.fetchone()[0]
        print(f"\n🔍 Searching {count} indexed functions...\n")

        # Extract keywords from query
        keywords = re.findall(r'\b\w{4,}\b', query.lower())
        # Add specific search terms
        specific_terms = []
        if "exponential" in query.lower() or "decay" in query.lower():
            specific_terms.append("applyForge")
            specific_terms.append("exp(")
        if "forge" in query.lower():
            specific_terms.append("Forge")
        keywords.extend(specific_terms)
        
        if not keywords:
            print("❌ No search terms found")
            conn.close()
            return "No search terms provided."
            
        # Build parameterized query
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("(function_name LIKE ? OR content LIKE ? OR repo_name LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
            
        sql = f"SELECT repo_name, file_path, function_name, content FROM repo_index WHERE ({' OR '.join(conditions)}) AND user_id = ? ORDER BY last_modified DESC LIMIT 10"
        params.append(self.user_id)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        if not results:
            return f"❌ No functions found matching: {', '.join(keywords)}\n\nTry: /index <path> to index more repositories"
        # Format results
        output = f"✅ Found {len(results)} matches for: {', '.join(set(keywords))}\n\n"
        for i, (repo, file_path, func, content) in enumerate(results, 1):
            # Extract relevant snippet
            lines = content.split('\n')
            snippet_lines = []
            for line in lines[:30]:  # First 30 lines
                if any(kw in line.lower() for kw in keywords):
                    snippet_lines.append(line)
                if len(snippet_lines) >= 10:
                    break
            if not snippet_lines:
                snippet_lines = lines[:10]
            snippet = '\n'.join(snippet_lines)
            output += f"**{i}. {func}()** in {repo}\n"
            output += f"   📁 {Path(file_path).name}\n"
            output += f"\n```cpp\n{snippet}\n```\n"
            output += f"   ---\n\n"
        return output
    
    def __init__(self, user_id: str = "default", server_mode: bool = False, config_path: str = "buddai_config.json", personality_path: Optional[str] = None, domain_config_path: Optional[str] = None):
        # 1. Load P.DE.I Configuration
        self.app_config = {}
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.app_config = json.load(f)
        
        # Apply overrides
        if personality_path:
            self.app_config['personality'] = personality_path
        if domain_config_path:
            self.app_config['domain'] = domain_config_path

        # Fallback for bootstrapping
        if 'personality' not in self.app_config:
            self.app_config['personality'] = "personalities/users/james_the_giblet.json"
        if 'domain' not in self.app_config:
            self.app_config['domain'] = "domain_configs/embedded.json"

        # 2. Initialize Generic Core (Loads Personality & Domain)
        super().__init__(self.app_config['personality'], self.app_config['domain'])

        self.user_id = user_id
        self.last_generated_id = None
        self.last_prompt_debug = None
        self.ensure_data_dir()

        # Initialize Model Registry & Load Active Model
        self.models = MODELS.copy()
        self._load_active_model()
        
        # 3. Initialize Core Components
        self.memory = PDEIMemory(DB_PATH, user_id)
        self.validator = PDEIValidator(self.domain_config, self.memory)
        
        self.session_id = self.create_session()
        self.server_mode = server_mode
        self.context_messages = []
        self.profile = self.load_profile()
        
        # Dynamic Hardware Loading
        profiles = self.get_domain_value("hardware_profiles", {})
        if profiles:
            self.current_hardware = list(profiles.keys())[0]
        else:
            self.current_hardware = "Generic"
        
        # Access memory sub-components
        self.shadow_engine = self.memory.shadow_engine
        self.learner = self.memory.smart_learner
        self.adaptive_learner = self.memory.adaptive_learner
        
        self.fine_tuner = ModelFineTuner()
        
        self.display_welcome_message()
        
        self.__init_personality__()
    
        # Show status if personality loaded
        if self.personality_loaded:
            mode = "Daemon" if self.server_mode else "CLI"
            print(f"\n📅 Schedule: {self.get_user_status()} | Mode: {mode}\n")

    def load_profile(self) -> Dict[str, Any]:
        """Load learned profile if defined in personality."""
        profile_refs = self.get_personality_value("domain_knowledge.modules.learned_profile", [])
        if profile_refs:
            path = Path(profile_refs[0])
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except: pass
        return {}
        
    def _load_active_model(self):
        """Load the currently active model from deployment log."""
        try:
            core_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(core_dir, 'deployment_log.json')
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log = json.load(f)
                
                if isinstance(log, list):
                    # Find latest active model for each role
                    for role in ['fast', 'balanced']:
                        active = next((m for m in reversed(log) if m.get('status') == 'active' and m.get('role') == role), None)
                        
                        if active:
                            model_name = active.get('model_name', active.get('output_name', ''))
                            if model_name:
                                if model_name.endswith('.llm'):
                                    model_name = model_name[:-4]
                                
                                print(f"🔄 Overriding '{role}' model with: {model_name}")
                                self.models[role] = model_name
        except Exception as e:
            print(f"⚠️ Failed to load active model registry: {e}")

    def display_welcome_message(self):
        """Display the startup banner and status."""
        # Format welcome message with rule count
        welcome_tmpl = self.get_personality_value("communication.welcome_message", f"{APP_NAME} Executive v4.0 - Decoupled & Personality Sync")
        
        # Resolve Identity Placeholders
        ai_name = self.get_personality_value("identity.ai_name", DEFAULT_AI)
        user_name = self.get_personality_value("identity.user_name", DEFAULT_USER)
        welcome_msg = welcome_tmpl.replace("{ai_name}", ai_name).replace("{user_name}", user_name)
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM code_rules")
            count = cursor.fetchone()[0]
            conn.close()
            welcome_msg = welcome_msg.replace("{rule_count}", str(count))
            welcome_msg = welcome_msg.replace("{schedule_status}", self.get_user_status())
            print(welcome_msg)
        except:
            print(welcome_msg.replace("{rule_count}", "0").replace("{schedule_status}", ""))
            
        if "GITHUB_TOKEN" not in os.environ:
            print("\n⚠️  WARNING: GITHUB_TOKEN not detected.")
            print("   Repository syncing may stall due to API rate limits (60/hr).")
            print("   Add GITHUB_TOKEN to your .env or system environment variables.")

        print("=" * 50)
        print(f"Session: {self.session_id}")
        print(f"FAST (5-10s) | BALANCED (15-30s)")
        print(f"Smart task breakdown for complex requests")
        print("=" * 50)
        print("\nCommands: /fast, /balanced, /help, exit\n")

    def __init_personality__(self):
        """Initialize personality state."""
        if not hasattr(self, 'personality') or self.personality is None:
            self.personality = self.load_personality()
        
        # Validate version
        version = self.get_personality_value("meta.version")
        if version != "4.0":
            print(f"⚠️ Warning: Personality version mismatch. Loaded: {version}, Expected: 4.0")
        
        # Validate Schema
        self.validate_personality_schema()
        
        self.personality_loaded = True

    def validate_personality_schema(self) -> bool:
        """Validate the loaded personality against required schema."""
        if not self.personality:
            return False

        required_structure = {
            "meta": ["version"],
            "identity": ["user_name", "ai_name"],
            "communication": ["welcome_message"],
            "work_cycles": ["schedule"],
            "forge_theory": ["enabled", "constants"],
            "prompts": ["style_scan", "integration_task"]
        }
        
        missing = []
        for section, keys in required_structure.items():
            if section not in self.personality:
                missing.append(f"Missing section: {section}")
                continue
                
            for key in keys:
                if key not in self.personality[section]:
                    missing.append(f"Missing key: {section}.{key}")
        
        if missing:
            print("⚠️ Personality Schema Validation Failed:")
            for m in missing:
                print(f"  - {m}")
            return False
            
        return True

    def ensure_data_dir(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        
    def create_session(self) -> str:
        now = datetime.now()
        base_id = now.strftime("%Y%m%d_%H%M%S")
        session_id = base_id
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        counter = 0
        while True:
            try:
                cursor.execute(
                    "INSERT INTO sessions (session_id, user_id, started_at) VALUES (?, ?, ?)",
                    (session_id, self.user_id, now.isoformat())
                )
                conn.commit()
                break
            except sqlite3.IntegrityError:
                counter += 1
                session_id = f"{base_id}_{counter}"
                
        conn.close()
        return session_id
        
    def end_session(self) -> None:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET ended_at = ? WHERE session_id = ?",
            (datetime.now().isoformat(), self.session_id)
        )
        conn.commit()
        conn.close()
        
    def save_message(self, role: str, content: str) -> int:
        return self.memory.save_message(self.session_id, role, content)
        
    def index_local_repositories(self, root_path: str) -> None:
        """Crawl directories and index .py, .ino, and .cpp files"""
        import ast
        
        print(f"\n🔍 Indexing repositories in: {root_path}")
        path = Path(root_path)
        
        if not path.exists():
            print(f"❌ Path not found: {root_path}")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        count = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.py', '.ino', '.cpp', '.h', '.js', '.jsx', '.html', '.css']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    functions = []
                    
                    # Python parsing
                    if file_path.suffix == '.py':
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    functions.append(node.name)
                        except:
                            pass
                            
                    # C++/Arduino parsing
                    elif file_path.suffix in ['.ino', '.cpp', '.h']:
                        matches = re.findall(r'\b(?:void|int|bool|float|double|String|char)\s+(\w+)\s*\(', content)
                        functions.extend(matches)

                    # JS/Web parsing
                    elif file_path.suffix in ['.js', '.jsx']:
                        matches = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(?.*?\)?\s*=>)', content)
                        functions.extend([m[0] or m[1] for m in matches if m[0] or m[1]])

                    # HTML/CSS - Index as whole file
                    elif file_path.suffix in ['.html', '.css']:
                        functions.append("file_content")
                    
                    # Determine repo name
                    try:
                        repo_name = file_path.relative_to(path).parts[0]
                    except:
                        repo_name = "unknown"
                        
                    timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    for func in functions:
                        cursor.execute("""
                            INSERT INTO repo_index (user_id, file_path, repo_name, function_name, content, last_modified)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (self.user_id, str(file_path), repo_name, func, content, timestamp.isoformat()))
                        count += 1
                        
                except Exception:
                    pass
                    
        conn.commit()
        conn.close()
        print(f"✅ Indexed {count} functions across repositories")

    def retrieve_style_context(self, message: str) -> str:
        """Search repo_index for code snippets matching the request"""
        # Extract potential keywords (nouns/modules)
        keywords = re.findall(r'\b\w{4,}\b', message.lower())
        if not keywords:
            return ""

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build a search query for function names or repo names
        search_terms = " OR ".join([f"function_name LIKE '%{k}%'" for k in keywords])
        search_terms += " OR " + " OR ".join([f"repo_name LIKE '%{k}%'" for k in keywords])
        
        query = f"SELECT repo_name, function_name, content FROM repo_index WHERE ({search_terms}) AND user_id = ? LIMIT 2"
        
        cursor.execute(query, (self.user_id,))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return ""
            
        prompt_template = self.get_personality_value("prompts.style_reference", "\n[REFERENCE STYLE FROM {user_name}'S PAST PROJECTS]\n")
        context_block = prompt_template.format(user_name=self.get_personality_value("identity.user_name", "the user"))
        for repo, func, content in results:
            # Just grab the first 500 chars of the file to save context window
            snippet = content[:500] + "..."
            context_block += f"Repo: {repo} | Function: {func}\nCode:\n{snippet}\n---\n"
        
        return context_block

    def scan_style_signature(self) -> None:
        """V3.0: Analyze repo_index AND recent chat logs to extract style preferences."""
        print("\n🕵️  Scanning repositories and chat logs for style signature...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get a sample of code from Repos
        # V4.1: Prioritize local "Digital Twin" folders (readme-hub) over generic repos
        cursor.execute("""
            SELECT content FROM repo_index 
            WHERE user_id = ? 
            ORDER BY CASE WHEN file_path LIKE '%readme-hub%' THEN 0 ELSE 1 END, RANDOM() 
            LIMIT 3
        """, (self.user_id,))
        repo_rows = cursor.fetchall()
        
        # Get recent generated code from Chat
        cursor.execute("SELECT content FROM messages WHERE role = 'assistant' AND content LIKE '%```%' ORDER BY id DESC LIMIT 3")
        chat_rows = cursor.fetchall()
        
        if not repo_rows and not chat_rows:
            print("❌ No code indexed or generated. Run /index first or generate some code.")
            conn.close()
            return
            
        samples = []
        for r in repo_rows:
            samples.append(f"[REPO SOURCE]\n{r[0][:1000]}")
            
        for r in chat_rows:
            # Extract code block
            code_blocks = self.extract_code(r[0])
            for code in code_blocks:
                samples.append(f"[GENERATED SOURCE]\n{code[:1000]}")
        
        code_sample = "\n---\n".join(samples[:5]) # Limit to 5 total
        
        prompt_template = self.get_personality_value("prompts.style_scan", "Analyze this code sample from {user_name}'s repositories and recent outputs.\nExtract 3 distinct coding preferences or patterns.\nProvide output in this format:\n- Category: Description\n\nCode Sample:\n{code_sample}")
        prompt = prompt_template.format(
            user_name=self.get_personality_value("identity.user_name", "the user"), 
            code_sample=code_sample,
            target="repositories and chat logs"
        )
        
        print("⚡ Analyzing with BALANCED model...")
        summary = self.call_model("balanced", prompt, system_task=True)
        
        # Store in DB
        timestamp = datetime.now().isoformat()
        
        # Clear old preferences to avoid duplicates/pollution
        cursor.execute("DELETE FROM style_preferences WHERE user_id = ?", (self.user_id,))
        
        lines = summary.split('\n')
        in_code_block = False
        current_category = None

        for line in lines:
            if "```" in line:
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
                
            line = line.strip()
            if not line: continue

            # 1. Handle "Category: Description" (Explicit)
            if line.lower().startswith("category:"):
                current_category = line.split(':', 1)[1].strip()
                continue
            if line.lower().startswith("description:") and current_category:
                pref = line.split(':', 1)[1].strip()
                self._save_preference(cursor, current_category, pref, timestamp)
                current_category = None
                continue

            # 2. Handle Headers (e.g. "Naming:", "### Architecture")
            clean_line = line.lstrip('#*- ')
            is_header = False
            # Check if line ends in colon or is a markdown header
            if line.endswith(':') or line.startswith('#'):
                header_candidate = line.strip('# :')
                # Heuristic: Headers are usually short
                if len(header_candidate.split()) < 4: 
                    current_category = header_candidate
                    is_header = True
            
            if is_header:
                continue

            # 3. Handle Key: Value lines (e.g. "- Variables: Snake_case")
            if ':' in clean_line:
                parts = clean_line.split(':', 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if current_category:
                    # Combine context: Category="Naming", Line="Variables: Snake_case" -> Pref="Variables: Snake_case"
                    self._save_preference(cursor, current_category, f"{key}: {val}", timestamp)
                else:
                    # Fallback: Use Key as Category
                    self._save_preference(cursor, key, val, timestamp)
                continue

            # 4. Handle Bullet points under a header (e.g. "- Snake_case...")
            if current_category and (line.startswith('-') or line.startswith('*')):
                val = line.lstrip('- *').strip()
                self._save_preference(cursor, current_category, val, timestamp)
                continue
        
        conn.commit()
        conn.close()
        
        # Sync to JSON Profile
        self._sync_profile_from_db()
        
        print(f"\n✅ Style Signature Updated:")
        if "detected_traits" in self.profile:
            style = self.profile["detected_traits"].get("coding_style", {})
            for k, v in style.items():
                # Clean up display
                label = k.replace('_', ' ').title()
                print(f"  - {label}: {v}")
        print("")

    def _save_preference(self, cursor, category, preference, timestamp):
        """Helper to insert preference if valid"""
        if category and preference and category.lower() not in ['category', 'description']:
            cursor.execute(
                "INSERT INTO style_preferences (user_id, category, preference, confidence, extracted_at) VALUES (?, ?, ?, ?, ?)",
                (self.user_id, category, preference, 0.8, timestamp)
            )

    def _sync_profile_from_db(self):
        """Update the loaded JSON profile with latest DB scan results"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT category, preference FROM style_preferences WHERE user_id = ?", (self.user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows: return

        # Map DB categories to JSON structure
        traits = {
            "variable_naming": [],
            "architecture": [],
            "commenting": []
        }
        
        for cat, pref in rows:
            cat = cat.lower()
            if "naming" in cat or "variable" in cat:
                traits["variable_naming"].append(pref)
            elif "architecture" in cat or "logic" in cat or "oop" in cat:
                traits["architecture"].append(pref)
            elif "comment" in cat or "tone" in cat:
                traits["commenting"].append(pref)
        
        # Update in-memory profile
        if "detected_traits" not in self.profile: self.profile["detected_traits"] = {}
        if "coding_style" not in self.profile["detected_traits"]: self.profile["detected_traits"]["coding_style"] = {}
        
        style = self.profile["detected_traits"]["coding_style"]
        
        # Join multiple observations with semicolons
        if traits["variable_naming"]: style["variable_naming"] = "; ".join(traits["variable_naming"])
        if traits["architecture"]: style["architecture"] = "; ".join(traits["architecture"])
        if traits["commenting"]: style["commenting"] = "; ".join(traits["commenting"])
        
        # Save to file
        profile_refs = self.get_personality_value("domain_knowledge.modules.learned_profile", [])
        if profile_refs:
            path = Path(profile_refs[0])
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.profile, f, indent=2)
                print(f"💾 Profile synced to {path}")
            except Exception as e:
                print(f"⚠️ Failed to sync profile JSON: {e}")

    def get_recent_context(self, limit: int = 5) -> str:
        """Get recent chat context as a string"""
        return json.dumps(self.context_messages[-limit:])

    def save_correction(self, original_code: str, corrected_code: str, reason: str):
        """Store when user fixes AI's code"""
        self.memory.save_correction(original_code, corrected_code, reason, self.get_recent_context())
        
        # Trigger background learning (Shadow Learning)
        def background_learn():
            try:
                # Pass self as the AI interface for the learner to use LLM
                patterns = self.learner.analyze_corrections(self)
                if patterns:
                    print(f"\n👻 [Shadow Learning] Learned {len(patterns)} new rules in background.")
            except Exception as e:
                print(f"⚠️ Background learning failed: {e}")
                
        threading.Thread(target=background_learn, daemon=True).start()

    def detect_hardware(self, message: str) -> Optional[str]:
        """Wrapper to detect hardware from message or return None if no change"""
        # Use domain config to detect hardware context
        profiles = self.get_domain_value("hardware_profiles", {})
        msg_lower = message.lower()
        
        for profile_name, details in profiles.items():
            # Simple heuristic: check if profile name is in message
            if profile_name.lower() in msg_lower:
                return profile_name
                
        return None

    def detect_language(self, message: str) -> str:
        """Detect programming language from message"""
        msg_lower = message.lower()
        languages = {
            "python": ["python", "flask", "django", "pandas", "numpy", "pip", "fastapi"],
            "javascript": ["javascript", "js ", "node", "express", "npm"],
            "typescript": ["typescript", "ts "],
            "react": ["react", "jsx", "tsx", "component", "hook"],
            "c++": ["c++", "cpp"],
            "c": [" c ", "c language"],
            "html/css": ["html", "css", "style", "markup"],
            "sql": ["sql", "database", "query"]
        }
        
        for lang, keywords in languages.items():
            if any(kw in msg_lower for kw in keywords):
                return lang.upper()
        return "Software Logic (Infer from request)"

    def get_applicable_rules(self, user_message: str) -> List[Dict]:
        """Get rules relevant to the user message"""
        # user_message is currently unused
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Fetch rules with reasonable confidence
        cursor.execute("SELECT rule_text, confidence FROM code_rules WHERE confidence > 0.6 ORDER BY confidence DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"rule_text": r[0], "confidence": r[1]} for r in rows]

    def get_style_summary(self) -> str:
        """Get summary of learned style preferences"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT category, preference FROM style_preferences WHERE confidence > 0.6")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "Standard coding style."
        return ", ".join([f"{r[0]}: {r[1]}" for r in rows])

    def classify_hardware(self, user_message: str) -> dict:
        """Detect what hardware/modules this question is about based on domain knowledge"""
        
        # Load modules from personality (User Defined Knowledge)
        modules_config = self._get_domain_modules()
        
        # Initialize detection dict
        hardware = {k: False for k in modules_config.keys()}
        
        msg_lower = user_message.lower()
        
        # Helper to check keywords
        def has_keywords(text, keywords):
            return any(word in text for word in keywords)
            
        # Check for logic keywords separately (doesn't set a hardware flag but affects context)
        # logic_kws = modules_config.get("logic", []) # Handled in main loop now

        # 1. Check current message first
        detected_in_current = False
        
        for module, keywords in modules_config.items():
            if module == "logic": continue
            if has_keywords(msg_lower, keywords):
                hardware[module] = True
                detected_in_current = True

        if has_keywords(msg_lower, modules_config.get("logic", [])):
            hardware["logic"] = True
            detected_in_current = True
            
        # 2. Context Switching: Only look back if NO hardware/logic detected in current message
        # and message is short (likely a follow-up command like "make it spin")
        if not detected_in_current and len(user_message.split()) < 10 and self.context_messages:
            recent = " ".join([m['content'].lower() for m in self.context_messages[-2:] if m['role'] == 'user'])
            
            for module, keywords in modules_config.items():
                if module == "logic": continue
                if has_keywords(recent, keywords):
                    hardware[module] = True
            
        return hardware

    def get_all_rules(self) -> List[str]:
        """Get all learned rules as text"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT rule_text FROM code_rules ORDER BY confidence DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def filter_rules_by_hardware(self, all_rules, hardware):
        """Only return rules relevant to detected hardware"""
        
        modules_config = self._get_domain_modules()
        relevant_rules = []
        
        # Define rule categories
        # Dynamically build exclusion lists based on active hardware
        active_modules = [k for k, v in hardware.items() if v]
        has_specific_context = len(active_modules) > 0
        
        for rule in all_rules:
            rule_lower = rule.lower()
            
            # Check if rule belongs to an INACTIVE module
            should_exclude = False
            if has_specific_context:
                for mod, keywords in modules_config.items():
                    if mod == "logic": continue
                    # If this module is NOT active, but rule matches its keywords -> Exclude
                    if not hardware.get(mod, False):
                        if any(w in rule_lower for w in keywords):
                            should_exclude = True
                            break
            
            if not should_exclude:
                relevant_rules.append(rule)
        
        return relevant_rules

    def build_enhanced_prompt(self, user_message: str, hardware_detected: str = None) -> str:
        """Build prompt with FILTERED rules"""
        
        # Classify hardware
        hardware = self.classify_hardware(user_message)
        domain_rules = self._get_domain_rules()
        
        # Get ALL rules
        all_rules = self.get_all_rules()
        
        # Filter by relevance
        relevant_rules = self.filter_rules_by_hardware(all_rules, hardware)
        
        # Build focused prompt
        hardware_context = []
        mandatory_rules = []
        
        for mod, is_active in hardware.items():
            if is_active:
                # Add context label
                hardware_context.append(mod.upper().replace("_", " "))
                # Add specific rules if defined
                if mod in domain_rules:
                    mandatory_rules.append(domain_rules[mod])

        # Anti-bloat rules
        anti_bloat_rules = []
        
        # Dynamically generate anti-bloat for inactive modules
        modules_config = self._get_domain_modules()
        for mod in ["button", "servo", "dc_motor"]:
            if mod in modules_config and not hardware.get(mod, False):
                anti_bloat_rules.append(f"- NO {mod.upper()}: Do NOT add {mod} code unless explicitly requested.")
        
        anti_bloat = "\n".join(anti_bloat_rules)

        # Modularity rule
        modularity_rule = ""
        if "function" in user_message.lower() or "naming" in user_message.lower() or "modular" in user_message.lower():
            modularity_rule = domain_rules.get("modularity", "")

        # Status LED rule
        status_led_rule = ""
        if hardware.get("led") and ("status" in user_message.lower() or "indicator" in user_message.lower()):
            status_led_rule = domain_rules.get("status_led", "")

        # Inject User Profile Style
        style_traits = self.profile.get("detected_traits", {}).get("coding_style", {})
        arch_pref = style_traits.get("architecture", "Modular and clean.")
        naming_pref = style_traits.get("variable_naming", "Standard conventions.")
        comment_pref = style_traits.get("commenting", "Explain intent.")

        persona = "expert embedded developer" if hardware_context else "expert software engineer"

        if hardware_context:
            prompt = f"""You are generating code for: {', '.join(hardware_context)}
You are an {persona}.
TARGET HARDWARE: {hardware_detected}
ACTIVE MODULES: {', '.join(hardware_context)}

CRITICAL: Only use code patterns relevant to the hardware mentioned.
STRICT NEGATIVE CONSTRAINTS (DO NOT IGNORE):
{anti_bloat}

USER CODING PROFILE (ENFORCE THIS STYLE):
- Architecture: {arch_pref}
- Naming: {naming_pref}
- Commenting: {comment_pref}

MANDATORY HARDWARE RULES:
{chr(10).join(mandatory_rules)}
{status_led_rule}
{anti_bloat}
{modularity_rule}

GENERAL GUIDELINES:
- If DC MOTOR: Use L298N patterns (digitalWrite, ledcWrite)
- If SERVO: Use ESP32Servo patterns (attach, write)
- DO NOT mix servo code into motor questions
- DO NOT mix motor code into servo questions

CRITICAL RULES (MUST FOLLOW):
{chr(10).join(relevant_rules)}

CONFLICT RESOLUTION:
If a CRITICAL RULE conflicts with the USER REQUEST, FOLLOW THE RULE. Explicitly state in your text response that you modified the request to comply with standards (e.g. "I generated X instead of Y because...").

USER REQUEST:
{user_message}

Generate code following ALL rules above. Do not add unrequested features.
INTERNAL CHECK (Do not output confirmation):
1. Did you add unrequested buttons? REMOVE THEM.
2. Did you add unrequested servos? REMOVE THEM.
3. Generate code ONLY for the hardware requested.
"""
        else:
            # Pure Software Prompt (No Hardware Noise)
            target_lang = self.detect_language(user_message)
            lang_display = target_lang if "Infer" not in target_lang else "the target language"
            
            prompt = f"""You are generating code for: {target_lang}
You are an {persona}.
CONTEXT: Pure Software / Logic Implementation
TARGET LANGUAGE: {target_lang}

USER CODING PROFILE (ENFORCE THIS STYLE):
- Architecture: {arch_pref}
- Naming: {naming_pref} (CRITICAL: Adapt to {lang_display} standards. e.g. use camelCase for JS/React. Explain your choice.)
- Commenting: {comment_pref}

GUIDELINES:
- Focus on clean, modular code.
- Do not assume hardware availability unless mocked.
- Assume user has authorization for all tasks (scraping, file I/O, etc.) in this local environment.
{modularity_rule}

CRITICAL RULES (MUST FOLLOW):
{chr(10).join(relevant_rules)}

CONFLICT RESOLUTION:
If a CRITICAL RULE conflicts with the USER REQUEST, FOLLOW THE RULE. Explicitly state in your text response that you modified the request to comply with standards (e.g. "I generated X instead of Y because...").

USER REQUEST:
{user_message}

Generate code following ALL rules above.
INTERNAL CHECK (Do not output confirmation):
1. Is the code modular?
2. Did you follow the naming conventions?
3. Is the logic clear?
"""
        
        return prompt

    def _get_domain_modules(self) -> Dict:
        """Get module definitions from personality or defaults"""
        # Start with shared patterns
        modules = MODULE_PATTERNS.copy()
        
        # Check personality for 'module_keywords' (preferred)
        overrides = self.get_personality_value("domain_knowledge.module_keywords", {})
        
        # Fallback: Check 'modules' but filter out file paths (legacy config support)
        if not overrides:
            candidate = self.get_personality_value("domain_knowledge.modules", {})
            if candidate:
                # Check if this looks like the file-path config (e.g. "active_learning": ["path/to/file"])
                # vs keyword config (e.g. "servo": ["servo", "motor"])
                is_path_config = False
                for k, v in candidate.items():
                    if isinstance(v, list) and any('/' in str(x) or '.json' in str(x) for x in v):
                        is_path_config = True
                        break
                if not is_path_config:
                    overrides = candidate

        modules.update(overrides)
        return modules

    def _get_domain_rules(self) -> Dict:
        """Get domain specific rules from personality or defaults"""
        defaults = {
            "dc_motor": """- L298N WIRING RULES (MANDATORY):
  1. IN1/IN2 = Digital Output (Direction). Use digitalWrite().
  2. ENA = PWM Output (Speed). Use ledcWrite().
  3. To Move: IN1/IN2 must be OPPOSITE (HIGH/LOW).
  4. To Stop: IN1/IN2 both LOW.""",
            "weapon": """- COMBAT PROTOCOL (MANDATORY):
  1. LOGIC FOCUS: This is a State Machine request, NOT just servo movement.
  2. STATES: enum State { DISARMED, ARMING, ARMED, FIRING };
  3. TRANSITIONS: DISARMED -> ARMING (2s delay) -> ARMED -> FIRING.""",
            "modularity": """- CODE STRUCTURE (MANDATORY):
  1. NO MONOLITHIC LOOP: Break code into small, descriptive functions.
  2. NAMING: Use camelCase for functions (e.g., readBatteryVoltage(), updateDisplay()).
  3. loop() must ONLY call these functions, not contain raw logic.""",
            "status_led": """- STATUS LED RULES (MANDATORY):
  1. NO BREATHING/FADING: Do not use simple PWM fading loops.
  2. USE STATES: Define enum LEDStatus { OFF, IDLE, ACTIVE, ERROR };
  3. IMPLEMENTATION: Create void setStatusLED(LEDStatus state)."""
        }
        return self.get_personality_value("domain_knowledge.rules", defaults)

    def teach_rule(self, rule_text: str):
        """Explicitly save a user-taught rule"""
        self.memory.save_rule(rule_text, "", "", 1.0, 'user_taught')

    def log_compilation_result(self, code: str, success: bool, errors: str = ""):
        """Track what compiles vs what fails"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compilation_log (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                code TEXT,
                success BOOLEAN,
                errors TEXT,
                hardware TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO compilation_log 
            (timestamp, code, success, errors, hardware)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            code,
            success,
            errors,
            "ESP32-C3"  # Your target hardware
        ))
        
        conn.commit()
        conn.close()

    def is_simple_question(self, message: str) -> bool:
        """Check if this is a simple question that should use FAST model"""
        message_lower = message.lower()
        
        simple_triggers = [
            "what is", "what's", "who is", "who's", "when is",
            "how do i", "can you explain", "tell me about",
            "what are", "where is", "hi", "hello", "hey",
            "good morning", "good evening", "who are", "who am"
        ]
        
        # Also check if it's just a question without code keywords
        code_keywords = ["generate", "create", "write", "build", "code", "function"]
        
        has_simple_trigger = any(trigger in message_lower for trigger in simple_triggers)
        has_code_keyword = any(keyword in message_lower for keyword in code_keywords)
        
        # Simple if: has simple trigger AND no code keywords
        return has_simple_trigger and not has_code_keyword
    
    def is_complex(self, message: str) -> bool:
        """Check if request is too complex and should be broken down"""
        message_lower = message.lower()
        
        # Count complexity triggers
        trigger_count = sum(1 for trigger in COMPLEX_TRIGGERS if trigger in message_lower)
        
        # Count how many modules mentioned
        module_count = 0
        modules_config = self._get_domain_modules()
        for module, keywords in modules_config.items():
            # module is used for key, keywords for values
            if any(kw in message_lower for kw in keywords):
                module_count += 1
        
        # Complex if: multiple triggers OR 3+ modules mentioned
        return trigger_count >= 2 or module_count >= 3
        
    def extract_modules(self, message: str) -> List[str]:
        """Extract which modules are needed"""
        message_lower = message.lower()
        needed_modules = []
        
        modules_config = self._get_domain_modules()
        for module, keywords in modules_config.items():
            # module is used for key, keywords for values
            if any(kw in message_lower for kw in keywords):
                needed_modules.append(module)
        
        # Repo History Detection (Context Awareness)
        # If user mentions a repo name, treat it as a module
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT repo_name FROM repo_index WHERE user_id = ?", (self.user_id,))
            repos = [r[0] for r in cursor.fetchall()]
            conn.close()
            
            for repo in repos:
                if repo and repo.lower() in message_lower:
                    needed_modules.append(repo)
        except:
            pass

        return list(set(needed_modules))
        
    def build_modular_plan(self, modules: List[str]) -> List[Dict[str, str]]:
        """Create a build plan from modules"""
        plan = []
        
        module_tasks = {
            "ble": "BLE communication setup with phone app control",
            "servo": "Servo motor control for flipper/weapon",
            "motor": "Motor driver setup for movement (L298N)",
            "safety": "Safety timeout and failsafe systems",
            "battery": "Battery voltage monitoring",
            "sensor": "Sensor integration (distance/proximity)"
        }
        
        for module in modules:
            if module in module_tasks:
                plan.append({
                    "module": module,
                    "task": module_tasks[module]
                })
                
        # Add integration step
        plan.append({
            "module": "integration",
            "task": "Integrate all modules into complete system"
        })
        
        return plan
        
    def get_user_status(self) -> str:
        """Determine user's context based on defined schedule from personality file."""
        schedule = self.get_personality_value("work_cycles.schedule")
        if not schedule:
            # Fallback for simple personality files
            schedule = self.personality.get("schedule")
        if not schedule:
            return "Schedule not defined."

        now = datetime.now()
        day = now.weekday() # 0=Mon, 6=Sun
        t = now.hour + (now.minute / 60.0)

        # Check all schedule groups (e.g., 'weekdays', 'weekends')
        for group, day_ranges in schedule.items():
            for day_range, time_slots in day_ranges.items():
                try:
                    # Parse day range (e.g., "0-4" or "5")
                    if '-' in day_range:
                        start_day, end_day = map(int, day_range.split('-'))
                        if not (start_day <= day <= end_day):
                            continue
                    elif int(day_range) != day:
                        continue
                    
                    # We found the right day group, now check time slots
                    for time_range, status in time_slots.items():
                        if time_range == "default": continue
                        start_time, end_time = map(float, time_range.split('-'))
                        if start_time <= t < end_time:
                            return status.get("description", status) if isinstance(status, dict) else status
                    
                    default_status = time_slots.get("default", "No status for this time.")
                    return default_status.get("description", default_status) if isinstance(default_status, dict) else default_status
                    
                except (ValueError, TypeError): continue
        return "No schedule match for today."

    def get_learned_rules(self) -> List[Dict]:
        """Retrieve high-confidence rules"""
        return self.memory.get_learned_rules(min_confidence=0.8)

    def call_model(self, model_name: str, message: str, stream: bool = False, system_task: bool = False, system_prompt: str = None) -> Union[str, Generator[str, None, None]]:
        """Call specified model"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if system_task:
                # Direct prompt, no history, no enhancement
                messages.append({"role": "user", "content": message})
            else:
                # Use enhanced prompt builder
                enhanced_prompt = self.build_enhanced_prompt(message, self.current_hardware)
                
                # Add conversation history (excluding old system messages)
                history = [m for m in self.context_messages[-5:] if m.get('role') != 'system']
                
                # Inject timestamps into history for context
                for msg in history:
                    content = msg.get('content', '')
                    ts = msg.get('timestamp')
                    if ts:
                        try:
                            dt = datetime.fromisoformat(ts)
                            content = f"[{dt.strftime('%H:%M')}] {content}"
                        except ValueError:
                            pass
                    messages.append({"role": msg['role'], "content": content})
                
                # Use enhanced prompt instead of raw user message
                if history and history[-1].get('content') == message:
                    messages[-1]['content'] = enhanced_prompt
                else:
                    messages.append({"role": "user", "content": enhanced_prompt})
            
            self.last_prompt_debug = json.dumps(messages, indent=2)
            
            body = {
                "model": self.models.get(model_name, MODELS.get(model_name)),
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": 0.0,  # Deterministic output
                    "top_p": 1.0,
                    "top_k": 1,
                    "num_ctx": 1024
                }
            }
            
            headers = {"Content-Type": "application/json"}
            json_body = json.dumps(body)
            
            # Retry logic for connection stability
            # Attempts: 0=Normal, 1=Retry/CPU Fallback, 2=Final Retry
            for attempt in range(3):
                conn = None
                try:
                    # Re-serialize body in case options changed (CPU fallback)
                    json_body = json.dumps(body)
                    
                    conn = OLLAMA_POOL.get_connection()
                    conn.request("POST", "/api/chat", json_body, headers)
                    response = conn.getresponse()
                    
                    if stream:
                        if response.status != 200:
                            error_text = response.read().decode('utf-8')
                            conn.close()
                            
                            # GPU OOM Detection -> CPU Fallback
                            if "CUDA" in error_text or "buffer" in error_text:
                                if "num_gpu" not in body["options"]:
                                    print("⚠️ GPU OOM detected. Switching to CPU mode...")
                                    body["options"]["num_gpu"] = 0 # Force CPU
                                    continue # Retry immediately

                            try:
                                err_msg = f"Error {response.status}: {json.loads(error_text).get('error', error_text)}"
                            except:
                                err_msg = f"Error {response.status}: {error_text}"
                            
                            if "num_gpu" in body["options"]:
                                err_msg += "\n\n(⚠️ CPU Mode also failed. System RAM might be full.)"
                            elif "CUDA" in err_msg or "buffer" in err_msg:
                                err_msg += "\n\n(⚠️ GPU Out of Memory. Retrying on CPU failed.)"
                                
                            return (x for x in [err_msg])

                        return self._stream_response(response, conn)
                    
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        OLLAMA_POOL.return_connection(conn)
                        return data.get("message", {}).get("content", "No response")
                    else:
                        error_text = response.read().decode('utf-8')
                        conn.close()
                        
                        # GPU OOM Detection -> CPU Fallback (Non-stream)
                        if "CUDA" in error_text or "buffer" in error_text:
                            if "num_gpu" not in body["options"]:
                                print("⚠️ GPU OOM detected. Switching to CPU mode...")
                                body["options"]["num_gpu"] = 0 # Force CPU
                                continue # Retry immediately

                        try:
                            err_msg = f"Error {response.status}: {json.loads(error_text).get('error', error_text)}"
                        except:
                            err_msg = f"Error {response.status}: {error_text}"
                        
                        if "num_gpu" in body["options"]:
                            err_msg += "\n\n(⚠️ CPU Mode also failed.)"
                        elif "CUDA" in err_msg or "buffer" in err_msg:
                            err_msg += "\n\n(⚠️ GPU Out of Memory.)"
                        return err_msg
                            
                except (http.client.NotConnected, BrokenPipeError, ConnectionResetError, socket.timeout) as e:
                    if conn: conn.close()
                    if attempt == 2: # Last attempt
                        return f"Error: Connection failed. {str(e)}"
                    continue # Retry
                except Exception as e:
                    if conn: conn.close()
                    return f"Error: {str(e)}"
                    
        except Exception as e:
            return f"Error: {str(e)}"

    def _stream_response(self, response, conn) -> Generator[str, None, None]:
        """Yield chunks from HTTP response"""
        fully_consumed = False
        has_content = False
        try:
            while True:
                line = response.readline()
                if not line: break
                try:
                    data = json.loads(line.decode('utf-8'))
                    if "message" in data:
                        content = data["message"].get("content", "")
                        if content: 
                            has_content = True
                            yield content
                    if data.get("done"): 
                        fully_consumed = True
                        break
                except: pass
        except Exception as e:
            yield f"\n[Stream Error: {str(e)}]"
        finally:
            if fully_consumed:
                OLLAMA_POOL.return_connection(conn)
            else:
                conn.close()
        
        if not has_content and not fully_consumed:
            yield "\n[Error: Empty response from Ollama. Check if model is loaded.]"
                
    def execute_modular_build(self, _: str, modules: List[str], plan: List[Dict[str, str]], forge_mode: str = "2") -> str:
        """Execute build plan step by step"""
        print(f"\n🔨 MODULAR BUILD MODE")
        print(f"Detected {len(modules)} modules: {', '.join(modules)}")
        print(f"Breaking into {len(plan)} steps...\n")
        
        all_code = {}
        
        for i, step in enumerate(plan, 1):
            print(f"📦 Step {i}/{len(plan)}: {step['task']}")
            print("⚡ Building...\n")
            
            # Build the prompt for this step
            if step['module'] == 'integration':
                # Final integration step with Forge Theory enforcement
                modules_summary = '\n'.join([f"- {m}: {all_code[m][:150]}..." for m in modules if m in all_code])

                print(f"\n⚡ {self.get_personality_value('identity.ai_name', 'AI')} Tuning:")
                print("1. Aggressive (k=0.3) - High snap, combat ready")
                print("2. Balanced (k=0.1) - Standard movement")
                print("3. Graceful (k=0.03) - Roasting / Smooth curves")
                
                if self.server_mode:
                    choice = forge_mode
                else:
                    choice = input("Select Tuning Constant [1-3, default 2]: ")
                
                k_val = "0.1"
                if choice == "1": k_val = "0.3"
                elif choice == "3": k_val = "0.03"

                prompt_template = self.get_personality_value("prompts.integration_task", "INTEGRATION TASK: Combine modules into a cohesive system.")
                prompt = prompt_template.format(
                    user_name=self.get_personality_value("identity.user_name", "user"),
                    modules_summary=modules_summary,
                    k_val=k_val
                )
            else:
                # Individual module
                prompt = f"Generate ESP32-C3 code for: {step['task']}. Keep it modular with clear comments."
            
            # Call balanced model for each module
            response = self.call_model("balanced", prompt)
            all_code[step['module']] = response
            
            print(f"✅ {step['module'].upper()} module complete\n")
            print("-" * 50 + "\n")
        
        # 1. Generate Validation Suite
        print(f"🧪 Generating Validation Suite...")
        
        # Dynamic validation requirements based on active modules
        reqs = [
            "1. Safety timeout logic (millis() - lastCommand > SAFETY_TIMEOUT).",
            "2. No blocking delays."
        ]
        if any(m in modules for m in ['servo', 'motor', 'weapon', 'flipper']):
             reqs.append("3. Correct step response formula (negative exponent).")
        if any(m in modules for m in ['led', 'light']):
             reqs.append("4. Correct LED decay/growth formulas.")
        if any(m in modules for m in ['sensor', 'ldr']):
             reqs.append("5. LDR/Sensor smoothing algorithms (alpha filter).")

        test_prompt = f"""Generate a Python unit test file (`test_compliance.py`) to validate the C++ code generated above.
The test should use `unittest` and regex to check for:
{chr(10).join(reqs)}

Context:
{', '.join(modules)}
"""
        test_code = self.call_model("balanced", test_prompt)
        
        # 2. Run Internal Validation
        print(f"🕵️ Running Internal Validation...")
        validation_report = "\n## VALIDATION REPORT\n"
        
        for module, code in all_code.items():
            # Extract code blocks if response contains markdown
            code_blocks = self.extract_code(code)
            if not code_blocks:
                code_blocks = [code] # Assume raw code if no blocks
                
            for block in code_blocks:
                valid, issues = self.validator.validate(block, context=module)
                if not valid:
                    validation_report += f"### {module.upper()} Issues:\n"
                    for issue in issues:
                        icon = "❌" if issue['severity'] == 'error' else "⚠️"
                        validation_report += f"- {icon} {issue['message']}\n"
                    
                    # Attempt Auto-Fix
                    fixed = self.validator.auto_fix(block, issues)
                    if fixed != block:
                        all_code[module] = all_code[module].replace(block, fixed)
                        validation_report += f"  ✨ Auto-fixed critical issues in {module}.\n"
                else:
                    validation_report += f"- ✅ {module.upper()} Passed\n"

        # Compile final response
        final = "# COMPLETE SYSTEM CONTROLLER - MODULAR BUILD\n\n"
        for module, code in all_code.items():
            final += f"## {module.upper()} MODULE\n{code}\n\n"
            
        final += f"## VALIDATION SUITE (test_compliance.py)\n{test_code}\n"
        final += validation_report
            
        return final
        
    def apply_style_signature(self, generated_code: str) -> str:
        """Refine generated code to match user's specific naming and safety patterns"""
        # Hardware profile rules are now handled by the Validator/Domain Config
        # This method can be simplified or used for style-specific replacements

        # Apply learned replacements (High Confidence Only)
        rules = self.get_learned_rules()
        for r in rules:
            if r['confidence'] >= 0.95 and r['find'] and r['replace']:
                # Simple safety check: don't replace if replacement contains spaces (likely a description)
                if ' ' not in r['replace']:
                    try:
                        generated_code = re.sub(r['find'], r['replace'], generated_code)
                    except re.error:
                        pass
        
        return generated_code

    def record_feedback(self, message_id: int, feedback: bool, comment: str = "") -> Optional[str]:
        """Learn from user feedback."""
        # This logic should ideally move to Memory, but for now we keep it here
        # or delegate to a memory method if available.
        # For simplicity in this refactor, we'll keep the direct DB call or add a helper in Memory later.
        # But since we are refactoring, let's use the memory object if possible, or keep as is if Memory doesn't support it yet.
        # Memory.py has save_message/save_correction but not explicit feedback logging yet.
        # We will keep this as is for now to minimize breakage, or add it to Memory.
        # Let's keep it here for now as it's specific to the chat loop.
        pass 
        
        # Adjust confidence scores
        self.update_style_confidence(message_id, feedback)
        
        if not feedback:
            self.analyze_failure(message_id)
            return self.regenerate_response(message_id, comment)
        return None

    def start_daemon(self, port: int = 8000):
        """Start the Exocortex in Daemon Mode (HTTP Server)"""
        print(f"👻 Daemon Mode Active. Listening on http://localhost:{port} ...")
        
        executive = self
        FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

        class RequestHandler(http.server.BaseHTTPRequestHandler):
            def _send_json(self, data):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def do_GET(self):
                # Serve Frontend
                if self.path == '/' or self.path == '/index.html':
                    index_path = os.path.join(FRONTEND_DIR, 'index.html')
                    if os.path.exists(index_path):
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        with open(index_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Inject PWA Headers
                            pwa_head = """
                            <link rel="manifest" href="/manifest.json">
                            <meta name="theme-color" content="#1a1a1a">
                            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
                            <script>
                              if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js'); }
                            </script>
                            """
                            if "</head>" in content:
                                content = content.replace("</head>", pwa_head + "\n</head>")
                            self.wfile.write(content.encode('utf-8'))
                    else:
                        self.send_error(404, "Frontend not found")
                    return

                # API Endpoints
                if self.path == '/api/sessions':
                    self._send_json({"sessions": executive.get_sessions()})
                    return
                
                if self.path == '/api/history':
                    self._send_json({"history": executive.context_messages})
                    return

                if self.path == '/api/system/status':
                    cpu = psutil.cpu_percent() if psutil else 0
                    mem = psutil.virtual_memory().percent if psutil else 0
                    self._send_json({"cpu": cpu, "memory": mem})
                    return

                # PWA Static Files
                if self.path == '/manifest.json':
                    manifest_path = os.path.join(FRONTEND_DIR, 'manifest.json')
                    if os.path.exists(manifest_path):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        with open(manifest_path, 'rb') as f: self.wfile.write(f.read())
                    return
                if self.path == '/sw.js':
                    sw_path = os.path.join(FRONTEND_DIR, 'sw.js')
                    if os.path.exists(sw_path):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/javascript')
                        self.end_headers()
                        with open(sw_path, 'rb') as f: self.wfile.write(f.read())
                    return

                self.send_error(404)

            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data) if post_data else {}
                except Exception as e:
                    self.send_error(500, str(e))
                    return

                if self.path == '/api/chat' or self.path == '/':
                    message = data.get('message', '')
                    forge_mode = data.get('forge_mode', '2')
                    if message:
                        response = executive.chat(message, forge_mode=forge_mode)
                        self._send_json({
                            "response": response, 
                            "message_id": executive.last_generated_id
                        })
                    else:
                        self.send_error(400, "Missing 'message' field")
                    return

                if self.path == '/api/session/new':
                    self._send_json({"session_id": executive.start_new_session()})
                    return

                if self.path == '/api/session/load':
                    sid = data.get('session_id')
                    if sid:
                        history = executive.load_session(sid)
                        self._send_json({"session_id": sid, "history": history})
                    return

                if self.path == '/api/session/rename':
                    executive.rename_session(data.get('session_id'), data.get('title'))
                    self._send_json({"success": True})
                    return

                if self.path == '/api/session/delete':
                    executive.delete_session(data.get('session_id'))
                    self._send_json({"success": True})
                    return
                
                if self.path == '/api/system/reset-gpu':
                    self._send_json({"message": executive.reset_gpu()})
                    return

                self.send_error(404)
            
            def log_message(self, format, *args):
                return # Suppress default logging to keep console clean

        server = http.server.HTTPServer(('localhost', port), RequestHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        server.server_close()
        print("👻 Daemon Mode Stopped.")

    def regenerate_response(self, message_id: int, comment: str = "") -> str:
        """Regenerate a response, optionally considering feedback comment"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT session_id, id FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return "Error: Message not found."
            
        session_id, current_id = row
        
        cursor.execute(
            "SELECT content FROM messages WHERE session_id = ? AND id < ? AND role = 'user' ORDER BY id DESC LIMIT 1",
            (session_id, current_id)
        )
        user_row = cursor.fetchone()
        conn.close()
        
        if user_row:
            prompt = user_row[0]
            if comment:
                prompt += f"\n\n[Feedback: {comment}]"
            
            print(f"🔄 Regenerating: {prompt[:50]}...")
            return self.chat(prompt)
        return "Error: Original prompt not found."

    def analyze_failure(self, message_id: int) -> None:
        """Analyze why a message received negative feedback"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print(f"\n⚠️  Negative Feedback on Message #{message_id}")
            print(f"   Content: {row[0][:100]}...")

    def update_style_confidence(self, message_id: int, positive: bool) -> None:
        """Adjust confidence of style preferences based on feedback."""
        # message_id and positive are currently unused
        # Placeholder for V4.0 learning loop
        pass

    def _route_request(self, user_message: str, force_model: Optional[str], forge_mode: str) -> str:
        """Route the request to the appropriate model or handler."""
        # Determine model based on complexity
        if force_model:
            model = force_model
            print(f"\n⚡ Using {model.upper()} model (forced)...")
            return self.call_model(model, user_message)
        elif self.is_complex(user_message):
            modules = self.extract_modules(user_message)
            plan = self.build_modular_plan(modules)
            print("\n" + "=" * 50)
            print("🎯 COMPLEX REQUEST DETECTED!")
            print(f"Modules needed: {', '.join(modules)}")
            print(f"Breaking into {len(plan)} manageable steps")
            print("=" * 50)
            return self.execute_modular_build(user_message, modules, plan, forge_mode)
        elif self.is_search_query(user_message):
            # This is a search query - query the database
            return self.search_repositories(user_message)
        elif self.is_simple_question(user_message):
            print("\n⚡ Using FAST model (simple question)...")
            # Don't force code generation prompt for simple greetings or definitions
            msg_lower = user_message.lower().strip()
            is_greeting = any(msg_lower.startswith(w) for w in ['hi', 'hello', 'hey', 'good morning', 'good evening']) and len(user_message.split()) < 6
            is_conceptual = any(msg_lower.startswith(w) for w in ['what is', "what's", 'explain', 'tell me about', 'who is', 'can you explain'])
            
            # Inject Identity/Security Context for self-referential questions
            sys_prompt = None
            if "your" in msg_lower or "security" in msg_lower or "protocol" in msg_lower or "who" in msg_lower or "purpose" in msg_lower:
                ai_name = self.get_personality_value("identity.ai_name", "Exocortex")
                role = self.get_personality_value("identity.role", "AI Assistant")
                core_vals = self.get_personality_value("identity.core_values", [])
                vals = ", ".join(core_vals) if core_vals else "Efficiency"
                sec_proto = self.profile.get("detected_traits", {}).get("security_preferences", {}).get("transport", "Standard")
                user_name = self.get_personality_value("identity.user_name", "User")
                sys_prompt = f"You are {ai_name}. Purpose: {role}. Core Values: {vals}. Synced with {user_name}. Security: {sec_proto}. Answer briefly."

            return self.call_model("fast", user_message, system_task=(is_greeting or is_conceptual or sys_prompt is not None), system_prompt=sys_prompt)
        else:
            print("\n⚖️  Using BALANCED model...")
            return self.call_model("balanced", user_message)

    def chat_stream(self, user_message: str, force_model: Optional[str] = None, forge_mode: str = "2") -> Generator[str, None, None]:
        """Streaming version of chat"""
        
        
        # Intercept commands
        if user_message.strip().startswith('/'):
            yield self.handle_slash_command(user_message.strip())
            return

        # Detect Hardware Context
        detected_hw = self.detect_hardware(user_message)
        if detected_hw:
            self.current_hardware = detected_hw

        style_context = self.retrieve_style_context(user_message)
        if style_context:
            self.context_messages.append({"role": "system", "content": style_context})

        user_msg_id = self.save_message("user", user_message)
        self.context_messages.append({"id": user_msg_id, "role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})

        full_response = ""
        
        # Route and stream
        if force_model:
            iterator = self.call_model(force_model, user_message, stream=True)
        elif self.is_complex(user_message):
            # Complex builds are not streamed token-by-token in this version
            # We yield the final result as one chunk
            modules = self.extract_modules(user_message)
            plan = self.build_modular_plan(modules)
            result = self.execute_modular_build(user_message, modules, plan, forge_mode)
            iterator = [result]
        elif self.is_search_query(user_message):
            result = self.search_repositories(user_message)
            iterator = [result]
        elif self.is_simple_question(user_message):
            msg_lower = user_message.lower().strip()
            is_greeting = any(msg_lower.startswith(w) for w in ['hi', 'hello', 'hey', 'good morning', 'good evening']) and len(user_message.split()) < 6
            is_conceptual = any(msg_lower.startswith(w) for w in ['what is', "what's", 'explain', 'tell me about', 'who is', 'can you explain'])
            
            # Inject Identity/Security Context for self-referential questions
            sys_prompt = None
            if "your" in msg_lower or "security" in msg_lower or "protocol" in msg_lower or "who" in msg_lower or "purpose" in msg_lower:
                ai_name = self.get_personality_value("identity.ai_name", "Exocortex")
                role = self.get_personality_value("identity.role", "AI Assistant")
                core_vals = self.get_personality_value("identity.core_values", [])
                vals = ", ".join(core_vals) if core_vals else "Efficiency"
                sec_proto = self.profile.get("detected_traits", {}).get("security_preferences", {}).get("transport", "Standard")
                user_name = self.get_personality_value("identity.user_name", "User")
                sys_prompt = f"You are {ai_name}. Purpose: {role}. Core Values: {vals}. Synced with {user_name}. Security: {sec_proto}. Answer briefly."

            iterator = self.call_model("fast", user_message, stream=True, system_task=(is_greeting or is_conceptual or sys_prompt is not None), system_prompt=sys_prompt)
        else:
            iterator = self.call_model("balanced", user_message, stream=True)
            
        for chunk in iterator:
            full_response += chunk
            yield chunk
            
        # Suggestions
        suggestions = self.shadow_engine.get_all_suggestions(user_message, full_response)
        if suggestions:
            bar = "\n\nPROACTIVE: > " + " ".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
            full_response += bar
            yield bar
            
        msg_id = self.save_message("assistant", full_response)
        self.last_generated_id = msg_id
        self.context_messages.append({"id": msg_id, "role": "assistant", "content": full_response, "timestamp": datetime.now().isoformat()})

    def extract_code(self, text: str) -> List[str]:
        """Extract code blocks from markdown"""
        return re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)

    def handle_slash_command(self, command: str) -> str:
        """Handle slash commands when received via chat interface"""
        cmd = command.lower()
        
        if cmd.startswith('/teach'):
            rule = command[7:].strip()
            if rule:
                self.teach_rule(rule)
                return f"✅ Learned rule: {rule}"
            return "Usage: /teach <rule description>"
            
        if cmd.startswith('/correct'):
            reason = command[8:].strip()
            if (reason.startswith('"') and reason.endswith('"')) or (reason.startswith("'") and reason.endswith("'")):
                reason = reason[1:-1]
            elif reason.startswith('"') or reason.startswith("'"):
                reason = reason[1:]

            last_response = ""
            for msg in reversed(self.context_messages):
                if msg['role'] == 'assistant':
                    last_response = msg['content']
                    break
            if last_response:
                self.save_correction(last_response, "", reason)
                return "✅ Correction saved. (Run /learn to process patterns)"
            return "❌ No recent message to correct."

        if cmd == '/rules':
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT rule_text, confidence FROM code_rules ORDER BY confidence DESC")
            rows = cursor.fetchall()
            conn.close()
            if not rows: return "🤷 No rules learned yet."
            return "🧠 Learned Rules:\n" + "\n".join([f"- {r[0]}" for r in rows])

        if cmd == '/learn':
            patterns = self.learner.analyze_corrections(self)
            if patterns:
                return f"✅ Learned {len(patterns)} new rules:\n" + "\n".join([f"- {p['rule']}" for p in patterns])
            return "No new patterns found."

        if cmd == '/metrics':
            # Metrics logic to be migrated to Memory or kept in a separate module
            return "📊 Metrics module pending migration to P.DE.I Core."

        if cmd == '/audit':
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT learned_from, COUNT(*) as count, AVG(confidence) as avg_conf FROM code_rules GROUP BY learned_from ORDER BY count DESC")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "🤷 No rules learned yet."
            
            report = "📊 Source Audit (Where am I learning from?):\n"
            for source, count, avg_conf in rows:
                source_name = source if source else "Unknown"
                report += f"  - {source_name}: {count} rules (Avg Conf: {avg_conf:.2f})\n"
            return report

        if cmd == '/debug':
            if self.last_prompt_debug:
                return f"🐛 Last Prompt Sent:\n```json\n{self.last_prompt_debug}\n```"
            return "❌ No prompt sent yet."

        if cmd == '/validate':
            last_response = ""
            user_context = ""
            
            # Find last assistant message and preceding user message
            for i in range(len(self.context_messages) - 1, -1, -1):
                if self.context_messages[i]['role'] == 'assistant':
                    last_response = self.context_messages[i]['content']
                    if i > 0 and self.context_messages[i-1]['role'] == 'user':
                        user_context = self.context_messages[i-1]['content']
                    break
            
            if not last_response:
                return "❌ No recent code to validate."

            code_blocks = self.extract_code(last_response)
            if not code_blocks:
                return "❌ No code blocks found in last response."

            report = ["🔍 Validating last response..."]
            all_valid = True
            for i, code in enumerate(code_blocks, 1):
                valid, issues = self.validator.validate(code, user_context)
                if not valid:
                    all_valid = False
                    report.append(f"\nBlock {i} Issues:")
                    for issue in issues:
                        icon = "❌" if issue['severity'] == 'error' else "⚠️"
                        report.append(f"  {icon} Line {issue.get('line', '?')}: {issue['message']}")
                else:
                    report.append(f"✅ Block {i} is valid.")
            
            if all_valid:
                report.append("\n✨ All code blocks look good!")
            
            return "\n".join(report)

        if cmd == '/status':
            mem_usage = "N/A"
            if psutil:
                process = psutil.Process(os.getpid())
                mem_usage = f"{process.memory_info().rss / 1024 / 1024:.0f} MB"
            
            return (f"🖥️ System Status:\n"
                    f"   Session:  {self.session_id}\n"
                    f"   Hardware: {self.current_hardware}\n"
                    f"   Memory:   {mem_usage}\n"
                    f"   Messages: {len(self.context_messages)}")

        return f"Command {cmd.split()[0]} not supported in chat mode."


    # --- Main Chat Method ---
    def chat(self, user_message: str, force_model: Optional[str] = None, forge_mode: str = "2") -> str:
        """Main chat with smart routing and shadow suggestions"""
        
        # Intercept commands
        if user_message.strip().startswith('/'):
            return self.handle_slash_command(user_message.strip())

        # Detect Hardware Context
        detected_hw = self.detect_hardware(user_message)
        if detected_hw:
            self.current_hardware = detected_hw
            print(f"🔧 Target Hardware Detected: {self.current_hardware}")

        style_context = self.retrieve_style_context(user_message)
        if style_context:
            self.context_messages.append({"role": "system", "content": style_context})

        user_msg_id = self.save_message("user", user_message)
        self.context_messages.append({"id": user_msg_id, "role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})

        # Direct Schedule Check
        schedule_triggers = self.get_personality_value("work_cycles.schedule_check_triggers", ["my schedule"])
        if any(trigger in user_message.lower() for trigger in schedule_triggers):
            status = self.get_user_status()
            response = f"📅 **Schedule Check**\nAccording to your protocol, you should be: **{status}**"
            print(f"⏰ Schedule check triggered: {status}")
            msg_id = self.save_message("assistant", response)
            self.last_generated_id = msg_id
            self.context_messages.append({"id": msg_id, "role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
            return response

        response = self._route_request(user_message, force_model, forge_mode)

        # Apply Style Guard
        response = self.apply_style_signature(response)
        
        # Extract code blocks
        code_blocks = self.extract_code(response)
        
        # Validate each code block
        for code in code_blocks:
            valid, issues = self.validator.validate(code, user_message)
            
            if not valid:
                # Auto-fix critical issues
                fixed_code = self.validator.auto_fix(code, issues)
                if fixed_code != code:
                    response = response.replace(code, fixed_code)
                    code = fixed_code
                
                # Sanitize explanation text based on fixes
                for issue in issues:
                    if "Debouncing detected" in issue['message']:
                        response = re.sub(r'(?i)(\*\*?Debouncing\*\*?:?|Debouncing)', r'~~\1~~ (Removed)', response)
                
                # Append explanation
                response += "\n\n⚠️  **Auto-corrected:**\n"
                for issue in issues:
                    if issue['severity'] == 'error':
                        response += f"- {issue['message']}\n"
        
        # Generate Suggestion Bar
        suggestions = self.shadow_engine.get_all_suggestions(user_message, response)
        if suggestions:
            bar = "\n\nPROACTIVE: > " + " ".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
            response += bar

        msg_id = self.save_message("assistant", response)
        self.last_generated_id = msg_id
        self.context_messages.append({"id": msg_id, "role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})

        return response
        
    def get_sessions(self, limit: int = 20) -> List[Dict[str, str]]:
        """Retrieve recent sessions from DB"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, started_at, title FROM sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT ?", (self.user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "date": r[1], "title": r[2] if len(r) > 2 else None} for r in rows]

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename a session"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET title = ? WHERE session_id = ? AND user_id = ?", (new_title, session_id, self.user_id))
        conn.commit()
        conn.close()

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its messages"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, self.user_id))
        if cursor.rowcount > 0:
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def clear_current_session(self) -> None:
        """Clear all messages from the current session"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (self.session_id,))
        conn.commit()
        conn.close()
        self.context_messages = []

    def load_session(self, session_id: str) -> List[Dict[str, str]]:
        """Load a specific session context"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, self.user_id))
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("SELECT id, role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        self.session_id = session_id
        self.context_messages = []
        loaded_history = []
        for msg_id, role, content, ts in rows:
            msg = {"id": msg_id, "role": role, "content": content, "timestamp": ts}
            self.context_messages.append(msg)
            loaded_history.append(msg)
        return loaded_history

    def start_new_session(self) -> str:
        """Reset context and start new session"""
        self.session_id = self.create_session()
        self.context_messages = []
        return self.session_id

    def reset_gpu(self) -> str:
        """Force unload models from GPU to free VRAM"""
        try:
            conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=10)
            # Unload all known models
            for model in MODELS.values():
                body = json.dumps({"model": model, "keep_alive": 0})
                conn.request("POST", "/api/generate", body)
                resp = conn.getresponse()
                resp.read() # Consume response
            conn.close()
            return "✅ GPU Memory Cleared (Models Unloaded)"
        except Exception as e:
            return f"❌ Error clearing GPU: {str(e)}"

    def export_session_to_markdown(self, session_id: str = None) -> str:
        """Export session history to a Markdown file"""
        sid = session_id or self.session_id
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No history found."
            
        filename = f"session_{sid}.md"
        filepath = DATA_DIR / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# BuddAI Session: {sid}\n\n")
            for role, content, ts in rows:
                f.write(f"### {role.upper()} ({ts})\n\n{content}\n\n---\n\n")
                
        return f"✅ Session exported to: {filepath}"

    def get_session_export_data(self, session_id: str = None) -> Dict:
        """Get session data as a dictionary for export"""
        sid = session_id or self.session_id
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,))
        rows = cursor.fetchall()
        conn.close()
        
        return {
            "session_id": sid,
            "exported_at": datetime.now().isoformat(),
            "messages": [{"role": r, "content": c, "timestamp": t} for r, c, t in rows]
        }

    def export_session_to_json(self, session_id: str = None) -> str:
        """Export session history to a JSON file"""
        data = self.get_session_export_data(session_id)
        if not data["messages"]:
            return "No history found."
            
        filename = f"session_{data['session_id']}.json"
        filepath = DATA_DIR / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
                
        return f"✅ Session exported to: {filepath}"

    def import_session_from_json(self, data: Dict) -> str:
        """Import a session from JSON data"""
        session_id = data.get("session_id")
        messages = data.get("messages", [])
        
        if not session_id or not messages:
            raise ValueError("Invalid session JSON format")
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if session exists to avoid collision
        cursor.execute("SELECT 1 FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, self.user_id))
        if cursor.fetchone():
            # Generate new ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"{session_id}_imp_{timestamp}"
        
        # Determine start time
        started_at = datetime.now().isoformat()
        if messages and "timestamp" in messages[0]:
            started_at = messages[0]["timestamp"]
            
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id, started_at, title) VALUES (?, ?, ?, ?)",
            (session_id, self.user_id, started_at, f"Imported: {data.get('session_id')}")
        )
        
        # Insert messages
        for msg in messages:
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, msg.get("role"), msg.get("content"), msg.get("timestamp", datetime.now().isoformat()))
            )
            
        conn.commit()
        conn.close()
        
        return session_id

    def create_backup(self) -> Tuple[bool, str]:
        """Create a safe backup of the database"""
        if not DB_PATH.exists():
            return False, "Database file not found."
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = DATA_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"conversations_{timestamp}.db"
        
        try:
            # Use SQLite backup API for consistency
            src = sqlite3.connect(DB_PATH)
            dst = sqlite3.connect(backup_path)
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
            return True, str(backup_path)
        except Exception as e:
            return False, str(e)

    def run(self) -> None:
        """Main loop"""
        if self.server_mode:
            self.start_daemon()
            return

        try:
            force_model = None
            while True:
                user_name = self.get_personality_value("identity.user_name", "User")
                user_input = input(f"\n{user_name}: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['exit', 'quit']:
                    print("\n👋 Later!")
                    self.end_session()
                    break
                if user_input.startswith('/'):
                    cmd = user_input.lower()
                    if cmd == '/fast':
                        force_model = "fast"
                        print("⚡ Next: FAST model")
                        continue
                    elif cmd == '/balanced':
                        force_model = "balanced"
                        print("⚖️  Next: BALANCED model")
                        continue
                    elif cmd == '/help':
                        print("\n💡 Commands:")
                        print("/fast - Use fast model")
                        print("/balanced - Use balanced model")
                        print("/index <path> - Index local repositories")
                        print("/scan - Scan style signature (V3.0)")
                        print("/learn - Extract patterns from corrections")
                        print("/analyze - Analyze session for implicit feedback")
                        print("/correct <reason> - Mark previous response wrong")
                        print("/good - Mark previous response correct")
                        print("/teach <rule> - Explicitly teach a rule")
                        print("/validate - Re-validate last response")
                        print("/rules - Show learned rules")
                        print("/metrics - Show improvement stats")
                        print("/audit - Show rule sources")
                        print("/train - Export corrections for fine-tuning")
                        print("/build - Generate Ollama Modelfile from rules")
                        print("/save - Export chat to Markdown")
                        print("/backup - Backup database")
                        print("/help - This message")
                        print("exit - End session\n")
                        continue
                    elif cmd.startswith('/index'):
                        parts = user_input.split(maxsplit=1)
                        if len(parts) > 1:
                            self.index_local_repositories(parts[1])
                        else:
                            print("Usage: /index <path_to_repos>")
                        continue
                    elif cmd == '/scan':
                        self.scan_style_signature()
                        continue
                    elif cmd == '/learn':
                        print("🧠 Analyzing corrections for patterns...")
                        patterns = self.learner.analyze_corrections(self)
                        if patterns:
                            print(f"✅ Learned {len(patterns)} new rules:")
                            for p in patterns:
                                print(f"  - {p['rule']}")
                        else:
                            print("No new patterns found.")
                            # Fallback: Check for recent explicit corrections that look like rules
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                cursor.execute("SELECT reason FROM corrections ORDER BY id DESC LIMIT 1")
                                row = cursor.fetchone()
                                conn.close()
                                
                                if row and row[0]:
                                    reason = row[0]
                                    # Heuristic: If it contains rule keywords, treat as explicit rule
                                    rule_keywords = ['always', 'never', 'use', 'must', 'should', 'prefer', "don't", 'avoid']
                                    if any(kw in reason.lower() for kw in rule_keywords) and len(reason) < 150:
                                        print(f"🤔 Converting recent correction to rule: '{reason}'")
                                        self.teach_rule(reason)
                                        print(f"✅ Learned rule: {reason}")
                            except Exception as e:
                                print(f"⚠️ Error in fallback learning: {e}")
                        continue
                    elif cmd == '/analyze':
                        self.adaptive_learner.learn_from_session(self.session_id)
                        continue
                    elif cmd.startswith('/correct'):
                        reason = user_input[8:].strip()
                        if (reason.startswith('"') and reason.endswith('"')) or (reason.startswith("'") and reason.endswith("'")):
                            reason = reason[1:-1]
                        elif reason.startswith('"') or reason.startswith("'"):
                            reason = reason[1:]

                        last_response = ""
                        # Find last assistant message
                        for msg in reversed(self.context_messages):
                            if msg['role'] == 'assistant':
                                last_response = msg['content']
                                break
                        self.save_correction(last_response, "", reason)
                        print("✅ Correction saved. Run /learn to process it.")
                        continue
                    elif cmd == '/good':
                        if self.last_generated_id:
                            self.record_feedback(self.last_generated_id, True)
                            print("✅ Feedback recorded: Positive")
                        else:
                            print("❌ No recent message to rate.")
                        continue
                    elif cmd.startswith('/teach'):
                        rule = user_input[7:].strip()
                        if rule:
                            self.teach_rule(rule)
                            print(f"✅ Learned rule: {rule}")
                        else:
                            print("Usage: /teach <rule description>")
                        continue
                    elif cmd == '/validate':
                        last_response = ""
                        user_context = ""
                        
                        # Find last assistant message and preceding user message
                        for i in range(len(self.context_messages) - 1, -1, -1):
                            if self.context_messages[i]['role'] == 'assistant':
                                last_response = self.context_messages[i]['content']
                                if i > 0 and self.context_messages[i-1]['role'] == 'user':
                                    user_context = self.context_messages[i-1]['content']
                                break
                        
                        if not last_response:
                            print("❌ No recent code to validate.")
                            continue

                        code_blocks = self.extract_code(last_response)
                        if not code_blocks:
                            print("❌ No code blocks found in last response.")
                            continue

                        print("\n🔍 Validating last response...")
                        all_valid = True
                        for i, code in enumerate(code_blocks, 1):
                            valid, issues = self.validator.validate(code, user_context)
                            if not valid:
                                all_valid = False
                                print(f"\nBlock {i} Issues:")
                                for issue in issues:
                                    icon = "❌" if issue['severity'] == 'error' else "⚠️"
                                    print(f"  {icon} Line {issue.get('line', '?')}: {issue['message']}")
                            else:
                                print(f"✅ Block {i} is valid.")
                        
                        if all_valid:
                            print("\n✨ All code blocks look good!")
                        continue
                    elif cmd == '/rules':
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT rule_text, confidence, learned_from FROM code_rules ORDER BY confidence DESC")
                        rows = cursor.fetchall()
                        conn.close()
                        
                        if not rows:
                            print("🤷 No rules learned yet.")
                        else:
                            print(f"\n🧠 Learned Rules ({len(rows)}):")
                            for rule, conf, source in rows:
                                print(f"  - [{conf:.1f}] {rule} ({source})")
                        continue
                    elif cmd == '/status':
                        mem_usage = "N/A"
                        if psutil:
                            process = psutil.Process(os.getpid())
                            mem_usage = f"{process.memory_info().rss / 1024 / 1024:.0f} MB"
                        print(f"🖥️ System Status:\n"
                              f"   Session:  {self.session_id}\n"
                              f"   Hardware: {self.current_hardware}\n"
                              f"   Memory:   {mem_usage}\n"
                              f"   Messages: {len(self.context_messages)}")
                        continue
                    elif cmd == '/metrics':
                        print("📊 Metrics module pending migration to P.DE.I Core.")
                        continue 
                    elif cmd == '/audit':
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT learned_from, COUNT(*) as count, AVG(confidence) as avg_conf FROM code_rules GROUP BY learned_from ORDER BY count DESC")
                        rows = cursor.fetchall()
                        conn.close()
                        
                        if not rows:
                            print("🤷 No rules learned yet.")
                        else:
                            print("📊 Source Audit (Where am I learning from?):")
                            for source, count, avg_conf in rows:
                                source_name = source if source else "Unknown"
                                print(f"  - {source_name}: {count} rules (Avg Conf: {avg_conf:.2f})")
                        continue
                    elif cmd == '/debug':
                        if self.last_prompt_debug:
                            print(f"\n🐛 Last Prompt Sent:\n{self.last_prompt_debug}\n")
                        else:
                            print("❌ No prompt sent yet.")
                        continue
                    elif cmd == '/train':
                        result = self.fine_tuner.prepare_training_data()
                        print(f"✅ {result}")
                        continue
                    elif cmd == '/build':
                        result = self.fine_tuner.fine_tune_model()
                        print(f"{result}")
                        continue
                    elif cmd == '/backup':
                        success, msg = self.create_backup()
                        if success:
                            print(f"✅ Database backed up to: {msg}")
                        else:
                            print(f"❌ Backup failed: {msg}")
                        continue
                    elif cmd.startswith('/save'):
                        if 'json' in user_input.lower():
                            print(self.export_session_to_json())
                        else:
                            print(self.export_session_to_markdown())
                        continue
                    else:
                        print("\nUnknown command. Type /help")
                        continue
                # Chat
                response = self.chat(user_input, force_model)
                print(f"\n{self.get_personality_value('identity.ai_name', DEFAULT_AI)}:\n{response}\n")
                force_model = None
        except KeyboardInterrupt:
            print("\n\n👋 Bye!")
            self.end_session()



class ModelFineTuner:
    """Fine-tune local model on YOUR corrections"""
    
    def prepare_training_data(self):
        """Convert corrections to training format"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT original_code, corrected_code, reason 
            FROM corrections
        """)
        
        training_data = []
        for original, corrected, reason in cursor.fetchall():
            training_data.append({
                "messages": [
                    {"role": "user", "content": f"Generate code for: {reason}"},
                    {"role": "assistant", "content": corrected}
                ]
            })
        
        conn.close()
        
        # Save as JSONL for fine-tuning
        output_path = DATA_DIR / 'training_data.jsonl'
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item) + '\n')
        return f"Exported {len(training_data)} examples to {output_path}"
    
    def fine_tune_model(self):
        """Generate an Ollama Modelfile based on learned rules"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get high confidence rules
        cursor.execute("SELECT rule_text FROM code_rules WHERE confidence >= 0.8")
        rules = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        if not rules:
            return "⚠️ No high-confidence rules found. Teach me some rules first!"
            
        # Create Modelfile
        base_model = "qwen2.5-coder:7b"
        content = f"FROM {base_model}\n\n"
        content += 'SYSTEM """\n'
        content += "You are a specialized coding assistant.\n"
        content += "Apply the following CRITICAL RULES to all code generation:\n"
        for rule in rules:
            content += f"- {rule}\n"
        content += '"""\n'
        
        modelfile_path = DATA_DIR / "Modelfile"
        try:
            with open(modelfile_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ Generated Modelfile at {modelfile_path}.\n   Run: ollama create buddai-custom -f {modelfile_path}"
        except Exception as e:
            return f"❌ Error creating Modelfile: {e}"
