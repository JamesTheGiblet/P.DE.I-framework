import os
import subprocess
import sys
import time

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

def run_step(script_name, description):
    print(f"\n{'='*60}")
    print(f"🚀 STEP: {description}")
    print(f"{'='*60}\n")
    
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Script not found at {script_path}")
        sys.exit(1)

    try:
        # Use sys.executable to ensure the same python interpreter is used
        subprocess.check_call([sys.executable, script_path])
        print(f"\n✅ {description} completed successfully.")
        time.sleep(1)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during {description}.")
        print(f"   Exit code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user.")
        sys.exit(1)

def main():
    print("\n" + "="*60)
    print("      P.DE.I FRAMEWORK - UNIFIED SETUP WIZARD")
    print("="*60)
    print("This wizard will guide you through the complete initialization process.")
    
    # Step 1: Sync Repositories
    print("\n[1/4] Knowledge Base Synchronization")
    if input("      Do you want to sync GitHub repositories? (y/n): ").strip().lower() == 'y':
        run_step("sync_repos.py", "Synchronize Knowledge Base")
    else:
        print("      ⏭️  Skipping repository sync.")

    # Step 2: Style Scan
    print("\n[2/4] Personality & Style Analysis")
    run_step("style_scanner.py", "Analyze Coding Style & Personality")

    # Step 3: Train Model
    print("\n[3/4] Model Training")
    run_step("train_model.py", "Train Personal Model Artifact")

    # Step 4: Deploy Model
    print("\n[4/4] Deployment")
    run_step("deploy_model.py", "Register & Deploy Model")

    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    # Step 5: Launch
    if input("\nWould you like to boot the Exocortex now? (y/n): ").strip().lower() == 'y':
        run_step("init_exocortex.py", "Boot Sequence")
    else:
        print("\nTo start later, run: python scripts/init_exocortex.py")

if __name__ == "__main__":
    main()