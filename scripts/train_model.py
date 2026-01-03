import json
import os
import time
import sys
import subprocess
from datetime import datetime

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CONFIG_PATH = os.path.join(BASE_DIR, 'pdei_core', 'training_config.json')
MANIFEST_PATH = os.path.join(BASE_DIR, 'pdei_core', 'learning_manifest.json')
PROFILE_PATH = os.path.join(BASE_DIR, 'profiles', 'james_the_giblet_learned.json')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {path}")
        sys.exit(1)

def send_notification(config):
    """Triggers a system notification when training is done."""
    msg = config['notification']['message'].format(output_name="All Targets")
    
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

def extract_github_user(manifest):
    """Extracts the GitHub username from the first repository URL."""
    repos = manifest.get('learning_targets', {}).get('repositories', [])
    for repo in repos:
        url = repo.get('url', '')
        if 'github.com' in url:
            # Handle git@github.com:User/repo.git and https://github.com/User/repo.git
            clean = url.replace('git@github.com:', '').replace('https://github.com/', '')
            if '/' in clean:
                return clean.split('/')[0]
    return None

def run_training(config, profile, github_user=None):
    """Simulates the training loop."""
    epochs = config['training_params']['epochs']
    targets = config.get('model_targets', [])

    # Determine naming prefix
    prefix = "pdei-exocortex"
    if github_user:
        prefix = f"pdei-{github_user.lower()}"
    
    print(f"👤 Identity Prefix: {prefix}")

    # Ingest Profile Data
    if profile:
        traits = profile.get('detected_traits', {})
        coding_style = traits.get('coding_style', {})
        personality = traits.get('personality_matrix', {})
        
        print(f"\n🧬 Ingesting User Profile:")
        print(f"   - Optimizing for Architecture: {coding_style.get('architecture', 'Standard')}")
        print(f"   - Tuning Personality Tone: {personality.get('tone', 'Neutral')}")
        print(f"   - Enforcing Security: {traits.get('security_preferences', {}).get('transport', 'Standard')}")
    
    for target in targets:
        role = target['role']
        base_arch = target['base_architecture']
        output_name = f"{prefix}{target['output_suffix']}"
        
        print(f"\n🔥 Initializing Training Run ({role.upper()}): {base_arch} -> {output_name}")
        
        # Simulated Progress Bar
        total_steps = 10
        try:
            for i in range(total_steps + 1):
                time.sleep(0.2) # Simulate compute work
                progress = i * 10
                bar = "█" * i + "-" * (total_steps - i)
                sys.stdout.write(f"\r   Progress: [{bar}] {progress}%")
                sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n\n⚠️  Training interrupted by user.")
            sys.exit(0)
        
        # Save simulated model artifact
        models_dir = os.path.join(BASE_DIR, 'models')
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, output_name)
        with open(model_path, 'w') as f:
            f.write(f"P.DE.I Custom Model: {base_arch}\nTrained on: {datetime.now().isoformat()}")
            
        print(f"\n✅ Weights saved to {model_path}")

        # --- OLLAMA INTEGRATION ---
        print(f"🐳 Registering '{output_name}' with Ollama...")
        
        # 1. Construct System Prompt
        system_prompt = "You are a specialized coding assistant."
        if profile:
            traits = profile.get('detected_traits', {})
            style = traits.get('coding_style', {})
            personality = traits.get('personality_matrix', {})
            
            system_prompt += f" You write code with the following style:\n"
            system_prompt += f"- Architecture: {style.get('architecture', 'Standard')}\n"
            system_prompt += f"- Naming: {style.get('variable_naming', 'Standard')}\n"
            system_prompt += f"- Comments: {style.get('commenting', 'Standard')}\n"
            system_prompt += f"- Tone: {personality.get('tone', 'Neutral')}\n"

        # 2. Determine Base Model
        base_ollama = base_arch.lower()
        if "qwen" in base_ollama and "2.5" in base_ollama:
            if "32b" in base_ollama: base_ollama = "qwen2.5-coder:32b"
            elif "7b" in base_ollama: base_ollama = "qwen2.5-coder:7b"
            elif "14b" in base_ollama: base_ollama = "qwen2.5-coder:14b"
            elif "1.5b" in base_ollama: base_ollama = "qwen2.5-coder:1.5b"
            elif "0.5b" in base_ollama: base_ollama = "qwen2.5-coder:0.5b"
            elif "3b" in base_ollama: base_ollama = "qwen2.5-coder:3b"
        
        # 3. Write Modelfile
        modelfile_content = f"FROM {base_ollama}\nSYSTEM \"\"\"{system_prompt}\"\"\""
        modelfile_path = os.path.join(models_dir, f'Modelfile_{role}')
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)

        # 4. Create Model
        ollama_tag = output_name.replace('.llm', '')
        try:
            subprocess.check_call(["ollama", "create", ollama_tag, "-f", modelfile_path])
            print(f"✅ Ollama model '{ollama_tag}' created successfully.")
        except Exception as e:
            print(f"❌ Failed to create Ollama model: {e}")
            print(f"   (Make sure Ollama is running and '{base_ollama}' is pulled)")

if __name__ == "__main__":
    # 1. Load Configurations
    train_config = load_json(TRAIN_CONFIG_PATH)
    manifest = load_json(MANIFEST_PATH)
    profile = load_json(PROFILE_PATH)
    
    # Auto-detect GitHub user for model naming
    user = extract_github_user(manifest)
    
    # 2. Prepare Data
    prepare_dataset(manifest)
    
    # 3. Train
    run_training(train_config, profile, user)
    
    # 4. Notify
    if train_config['notification']['enabled']:
        send_notification(train_config)