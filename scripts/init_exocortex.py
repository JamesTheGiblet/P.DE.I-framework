import json
import os
import time

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONALITY_PATH = os.path.join(BASE_DIR, 'personalities', 'exocortex_universal.json')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at {path}")
        return None

def boot_sequence():
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

    # 4. Output Welcome
    print("\n" + "="*50)
    welcome_msg = personality['communication']['welcome_message'].format(
        ai_name=personality['identity']['ai_name'],
        user_name=personality['identity']['user_name']
    )
    print(welcome_msg)
    print("="*50 + "\n")

if __name__ == "__main__":
    boot_sequence()