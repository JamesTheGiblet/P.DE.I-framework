#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def init_pdei(domain: str, user_name: str, ai_name: str = None):
    """Initialize a new P.DE.I instance"""
    
    if not ai_name:
        ai_name = f"{user_name}AI"
    
    # 1. Load domain config
    domain_path = Path(f"domain_configs/{domain}.json")
    if not domain_path.exists():
        print(f"❌ Domain config not found: {domain}")
        return
    
    # 2. Load personality template
    template_path = Path("personalities/template.json")
    with open(template_path) as f:
        personality = json.load(f)
    
    # 3. Fill in template
    personality['identity']['user_name'] = user_name
    personality['identity']['ai_name'] = ai_name
    personality['identity']['persona_description'] = f"{user_name}'s personal AI for {domain}"
    
    # 4. Save personality
    personality_file = f"{user_name.lower().replace(' ', '_')}_personality.json"
    personality_path = Path(f"personalities/{personality_file}")
    with open(personality_path, 'w') as f:
        json.dump(personality, f, indent=4)
    
    # 5. Create config.json
    config = {
        "framework": "P.DE.I v1.0",
        "instance_name": ai_name,
        "personality": str(personality_path),
        "domain": str(domain_path),
        "owner": user_name
    }
    
    config_file = f"{user_name.lower().replace(' ', '_')}_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"✅ P.DE.I instance created for {user_name}")
    print(f"   Config: {config_file}")
    print(f"   Personality: {personality_path}")
    print(f"   Domain: {domain}")
    print(f"\nRun: python main.py --config={config_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python setup.py <domain> <user_name> [ai_name]")
        print("Example: python setup.py pharma 'Dr. Sarah Chen' 'PharmaAI'")
        sys.exit(1)
    
    domain = sys.argv[1]
    user_name = sys.argv[2]
    ai_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    init_pdei(domain, user_name, ai_name)