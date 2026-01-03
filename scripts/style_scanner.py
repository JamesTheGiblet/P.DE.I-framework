import json
import os
import sys
from datetime import datetime

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(BASE_DIR, 'pdei_core', 'learning_manifest.json')
PROFILE_OUTPUT_PATH = os.path.join(BASE_DIR, 'profiles', 'user_learned_profile.json')

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def validate_secure_ops(manifest):
    """Enforces secure_ops rules: SSH transport only."""
    print("🔒 Validating Security Protocols...")
    security_context = manifest.get('security_context', {})
    
    if security_context.get('transport') != 'ssh':
        raise ValueError("Security Violation: Transport must be SSH.")

    for repo in manifest['learning_targets']['repositories']:
        url = repo['url']
        if not url.startswith('git@'):
            print(f"❌ Security Alert: Repository {repo['alias']} uses insecure transport ({url}).")
            print("   Rule: Repositories must be accessed via SSH (git@ pattern).")
            return False
        print(f"✅ Verified Secure Transport: {repo['alias']}")
    
    return True

def simulate_style_scan(manifest):
    """Simulates the AI analysis of code and text."""
    print("\n🧠 Initiating Exocortex Style Scan...")
    
    # In a real scenario, this would clone the repo and run NLP analysis.
    # Here we generate the profile based on the 'detected' traits.
    
    profile_data = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "source_manifest": "pdei_core/learning_manifest.json",
            "status": "active"
        },
        "detected_traits": {
            "coding_style": {
                "variable_naming": "Snake_case for variables, PascalCase for classes.",
                "architecture": "Functional-first logic wrapped in modular OOP structures.",
                "commenting": "High frequency. Focuses on 'Why' (intent)."
            },
            "personality_matrix": {
                "tone": "Pragmatic, direct, with dry technical humor.",
                "problem_solving": "Iterative. Prefers 'Make it work, then make it right'."
            }
        }
    }
    return profile_data

if __name__ == "__main__":
    manifest = load_json(MANIFEST_PATH)
    
    if validate_secure_ops(manifest):
        profile = simulate_style_scan(manifest)
        with open(PROFILE_OUTPUT_PATH, 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"\n✨ Profile generated at: {PROFILE_OUTPUT_PATH}")
    else:
        sys.exit(1)