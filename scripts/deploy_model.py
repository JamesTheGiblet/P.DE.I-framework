import json
import os
import sys
from datetime import datetime

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CONFIG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'training_config.json')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DEPLOY_LOG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'deployment_log.json')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at {path}")
        sys.exit(1)

def deploy_model():
    print("🚀 Initiating P.DE.I Model Deployment...")
    
    # 1. Load Training Config
    config = load_json(TRAIN_CONFIG_PATH)
    model_name = config['model_settings']['output_name']
    model_path = os.path.join(MODELS_DIR, model_name)
    
    # 2. Verify Artifact Exists
    if not os.path.exists(model_path):
        print(f"❌ Error: Model artifact '{model_name}' not found.")
        print("   Please run 'scripts/train_model.py' first.")
        sys.exit(1)
        
    print(f"📦 Found Artifact: {model_name}")
    print(f"   Size: {os.path.getsize(model_path)} bytes")
    
    # 3. Register Deployment
    deployment_record = {
        "deployed_at": datetime.now().isoformat(),
        "model_name": model_name,
        "base_architecture": config['model_settings']['base_architecture'],
        "status": "active",
        "location": f"models/{model_name}"
    }
    
    # Load existing log or create new
    log_data = []
    if os.path.exists(DEPLOY_LOG_PATH):
        try:
            with open(DEPLOY_LOG_PATH, 'r') as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    log_data.append(deployment_record)
    
    with open(DEPLOY_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    print(f"✅ Deployment Complete.")
    print(f"📝 Registry updated at: {DEPLOY_LOG_PATH}")
    print(f"🧠 System is now ready to infer using {model_name}")

if __name__ == "__main__":
    deploy_model()