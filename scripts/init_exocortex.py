import json
import os
import time
import sys
import argparse

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # Ensure pdei_core can be imported

PERSONALITY_PATH = os.path.join(BASE_DIR, 'personalities', 'james_the_giblet.json')
DEPLOY_LOG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'deployment_log.json')
DOMAIN_PATH = os.path.join(BASE_DIR, 'domain_configs', 'web_dev.json') # Default domain

from pdei_core.buddai_executive import BuddAI

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at {path}")
        return None

def boot_sequence():
    parser = argparse.ArgumentParser(description="P.DE.I Framework Bootloader")
    parser.add_argument("--daemon", action="store_true", help="Run in Daemon Mode (HTTP Server)")
    args = parser.parse_args()

    print("🔌 Initializing P.DE.I Framework...")
    time.sleep(0.5)
    
    # 1. Load Core Personality
    print(f"📂 Loading Personality: {os.path.basename(PERSONALITY_PATH)}")
    personality = load_json(PERSONALITY_PATH)
    if not personality: return

    # 2. Resolve Learned Profile
    # This checks the 'domain_knowledge' section for the profile we just linked
    profile_ref = personality.get('domain_knowledge', {}).get('modules', {}).get('learned_profile', [])
    
    if profile_ref:
        profile_path = os.path.join(BASE_DIR, profile_ref[0])
        print(f"🧠 Synaptic Link: Loading {profile_ref[0]}")
        profile = load_json(profile_path)
        
        # 3. Apply Traits (Adaptation)
        if profile:
            traits = profile.get('detected_traits', {}).get('personality_matrix', {})
            tone = traits.get('tone', 'Default')
            print(f"✨ Adaptation Complete. Tone set to: {tone}")
            print(f"🔒 Security Protocol: {profile.get('detected_traits', {}).get('security_preferences', {}).get('transport')}")

    # 4. Load Active Model
    print("⚙️  Checking Model Registry...")
    deploy_log = load_json(DEPLOY_LOG_PATH)
    active_model = None
    
    if deploy_log and isinstance(deploy_log, list):
        # Get the most recent active model
        active_model = next((m for m in reversed(deploy_log) if m.get('status') == 'active'), None)

    if active_model:
        print(f"🚀 Model Loaded: {active_model['model_name']} ({active_model['base_architecture']})")
    else:
        print("⚠️  No active model found. Running in fallback mode.")

    # 6. Handoff to Runtime
    print("\n🔌 Establishing Neural Link...")
    time.sleep(1)
    
    try:
        # Initialize the Executive
        bot = BuddAI(
            user_id="JamesTheGiblet",
            personality_path=PERSONALITY_PATH,
            domain_config_path=DOMAIN_PATH,
            server_mode=args.daemon
        )
        bot.run()
    except KeyboardInterrupt:
        print("\n🔌 Link Severed.")
    except Exception as e:
        print(f"\n❌ Runtime Error: {e}")

if __name__ == "__main__":
    boot_sequence()