#!/usr/bin/env python3
import argparse
import json
import sys
import shutil
import re
from pathlib import Path

# Ensure pdei_core can be imported
sys.path.append(str(Path(__file__).parent))

from pdei_core.memory import PDEIMemory
from pdei_core.shared import DATA_DIR, DB_PATH

def sanitize_filename(name: str) -> str:
    """Convert name to filesystem-safe string"""
    return re.sub(r'[^a-z0-9_]', '_', name.lower())

def init_instance(name: str, domain: str):
    print(f"🚀 Initializing P.DE.I instance for {name} ({domain})...")
    
    root_dir = Path(__file__).parent
    personalities_dir = root_dir / "personalities"
    domains_dir = root_dir / "domain_configs"
    
    # Ensure directories exist
    personalities_dir.mkdir(exist_ok=True)
    domains_dir.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    # 1. Create Personality
    safe_name = sanitize_filename(name)
    target_personality = personalities_dir / f"{safe_name}.json"
    template_path = personalities_dir / "template.json"
    
    # Check if template exists
    if not template_path.exists():
        # Try to find it in pdei_core if not in personalities (legacy location check)
        legacy_template = root_dir / "pdei_core" / "template.json"
        if legacy_template.exists():
            print(f"ℹ️  Found template in legacy location, copying to {template_path}...")
            shutil.copy(legacy_template, template_path)
    
    if template_path.exists():
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Customize fields
            data['meta']['author'] = name
            data['meta']['description'] = f"P.DE.I Assistant for {name}"
            data['identity']['user_name'] = name
            
            # Save new personality
            with open(target_personality, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Personality template created: {target_personality}")
        except Exception as e:
            print(f"❌ Error creating personality: {e}")
            return
    else:
        print(f"⚠️  Template not found at {template_path}. Creating minimal skeleton.")
        minimal_data = {
            "meta": {"version": "4.0", "author": name},
            "identity": {"user_name": name, "ai_name": "BuddAI"},
            "communication": {"welcome_message": "Hello {user_name}"},
            "work_cycles": {"schedule": {}},
            "forge_theory": {"enabled": False},
            "prompts": {},
            "domain_knowledge": {"modules": {}, "rules": {}}
        }
        with open(target_personality, 'w', encoding='utf-8') as f:
            json.dump(minimal_data, f, indent=2)
        print(f"✅ Created minimal personality: {target_personality}")

    # 2. Verify/Create Domain Config
    target_domain = domains_dir / f"{domain}.json"
    if not target_domain.exists():
        print(f"⚠️  Domain config not found: {target_domain}")
        print(f"   Creating placeholder for '{domain}'...")
        domain_data = {
            "domain": domain,
            "description": f"{domain} domain rules",
            "file_types": [],
            "validation_rules": {}
        }
        with open(target_domain, 'w', encoding='utf-8') as f:
            json.dump(domain_data, f, indent=2)
        print(f"✅ Created domain placeholder: {target_domain}")
    else:
        print(f"✅ Domain config loaded: {target_domain}")

    # 3. Initialize Database
    print("💽 Initializing database...")
    try:
        # This will create tables if they don't exist
        PDEIMemory(DB_PATH)
        print(f"✅ Database initialized: {DB_PATH}")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # 4. Update Main Config
    config_path = root_dir / "buddai_config.json"
    config_data = {
        "personality": str(target_personality.relative_to(root_dir)).replace("\\", "/"),
        "domain": str(target_domain.relative_to(root_dir)).replace("\\", "/")
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"✅ Configuration updated: {config_path}")
    print(f"\n✨ Ready to index repositories! Current State: {name} ({domain}) active.")

def main():
    parser = argparse.ArgumentParser(description="P.DE.I Setup & Bootstrap Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new P.DE.I instance")
    init_parser.add_argument("--name", required=True, help="User name (e.g. 'Dr. Sarah')")
    init_parser.add_argument("--domain", required=True, help="Domain name (e.g. 'pharma')")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_instance(args.name, args.domain)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()