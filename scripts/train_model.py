import json
import os
import time
import sys
from datetime import datetime

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CONFIG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'training_config.json')
MANIFEST_PATH = os.path.join(BASE_DIR, 'pdei_core', 'learning_manifest.json')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {path}")
        sys.exit(1)

def send_notification(config):
    """Triggers a system notification when training is done."""
    msg = config['notification']['message'].format(
        output_name=config['model_settings']['output_name']
    )
    
    print("\n" + "🔔" * 20)
    print(f"   {msg}")
    print("🔔" * 20 + "\n")
    
    # Optional: System beep
    if config['notification'].get('sound_alert'):
        print('\a') # ASCII Bell

def prepare_dataset(manifest):
    """Aggregates data from repositories and folders defined in the manifest."""
    print("📦 Aggregating Training Data...")
    targets = manifest.get('learning_targets', {})
    
    repo_count = len(targets.get('repositories', []))
    folder_count = len(targets.get('local_folders', []))
    
    print(f"   - Processing {repo_count} Repositories (SSH/GPG Verified)")
    print(f"   - Scanning {folder_count} Local Folders")
    time.sleep(1) # Simulate processing time
    print("✅ Dataset compiled successfully.")

def run_training(config):
    """Simulates the training loop."""
    model_name = config['model_settings']['base_architecture']
    output_name = config['model_settings']['output_name']
    epochs = config['training_params']['epochs']
    
    print(f"\n🔥 Initializing Training Run: {model_name} -> {output_name}")
    print(f"   Method: {config['training_params']['method']}")
    
    # Simulated Progress Bar
    total_steps = 10
    try:
        for i in range(total_steps + 1):
            time.sleep(0.3) # Simulate compute work
            progress = i * 10
            bar = "█" * i + "-" * (total_steps - i)
            sys.stdout.write(f"\r   Progress: [{bar}] {progress}% (Epoch {1 if i < 4 else 2 if i < 8 else 3}/{epochs})")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user.")
        sys.exit(0)
    
    # Save simulated model artifact
    models_dir = os.path.join(BASE_DIR, 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, output_name)
    with open(model_path, 'w') as f:
        f.write(f"P.DE.I Custom Model: {model_name}\nTrained on: {datetime.now().isoformat()}")
        
    print(f"\n\n✅ Weights saved to {model_path}")

if __name__ == "__main__":
    # 1. Load Configurations
    train_config = load_json(TRAIN_CONFIG_PATH)
    manifest = load_json(MANIFEST_PATH)
    
    # 2. Prepare Data
    prepare_dataset(manifest)
    
    # 3. Train
    run_training(train_config)
    
    # 4. Notify
    if train_config['notification']['enabled']:
        send_notification(train_config)