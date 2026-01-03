import json
import os
import sys
from datetime import datetime

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CONFIG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'training_config.json')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DEPLOY_LOG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'deployment_log.json')
MANIFEST_PATH = os.path.join(BASE_DIR, 'pdei_core', 'learning_manifest.json')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at {path}")
        sys.exit(1)

def extract_github_user(manifest):
    """Extracts the GitHub username from the first repository URL."""
    repos = manifest.get('learning_targets', {}).get('repositories', [])
    for repo in repos:
        url = repo.get('url', '')
        if 'github.com' in url:
            clean = url.replace('git@github.com:', '').replace('https://github.com/', '')
            if '/' in clean:
                return clean.split('/')[0]
    return None

def deploy_model():
    print("🚀 Initiating P.DE.I Model Deployment...")
    
    # 1. Load Training Config
    config = load_json(TRAIN_CONFIG_PATH)
    manifest = load_json(MANIFEST_PATH)
    targets = config.get('model_targets', [])
    
    # Determine prefix
    user = extract_github_user(manifest)
    prefix = f"pdei-{user.lower()}" if user else "pdei-exocortex"
    
    new_records = []

    for target in targets:
        output_name = f"{prefix}{target['output_suffix']}"
        model_path = os.path.join(MODELS_DIR, output_name)
        
        # 2. Verify Artifact Exists
        if not os.path.exists(model_path):
            print(f"❌ Error: Model artifact '{output_name}' not found.")
            continue
            
        print(f"📦 Found Artifact: {output_name} ({target['role']})")
        
        # 3. Register Deployment
        record = {
            "deployed_at": datetime.now().isoformat(),
            "model_name": output_name,
            "role": target['role'],
            "base_architecture": target['base_architecture'],
            "status": "active",
            "location": f"models/{output_name}"
        }
        new_records.append(record)
    
    # Load existing log or create new
    log_data = []
    if os.path.exists(DEPLOY_LOG_PATH):
        try:
            with open(DEPLOY_LOG_PATH, 'r') as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    log_data.extend(new_records)
    
    with open(DEPLOY_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    print(f"✅ Deployment Complete.")
    print(f"📝 Registry updated at: {DEPLOY_LOG_PATH}")
    print(f"🧠 System is now ready to infer using {len(new_records)} custom models.")

if __name__ == "__main__":
    deploy_model()