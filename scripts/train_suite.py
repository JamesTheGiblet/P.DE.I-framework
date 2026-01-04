import subprocess
import sys
import os

def run_command(cmd):
    print(f"\n⚡ Running: {cmd}")
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    print("🚀 P.DE.I Dual-Model Training Suite")
    print("===================================")
    
    # 1. Train Fast Model (1.5B)
    print("\n[1/6] Training FAST Model (1.5B)...")
    run_command(f"{sys.executable} scripts/fine_tune.py --role fast --epochs 3")
    
    # 2. Train Balanced Model (3B)
    print("\n[2/6] Training BALANCED Model (3B)...")
    run_command(f"{sys.executable} scripts/fine_tune.py --role balanced --epochs 3")
    
    # 3. Convert Fast Model
    print("\n[3/6] Registering FAST Model...")
    run_command(f"{sys.executable} scripts/convert_to_ollama.py --role fast --adapter models/pdei-exocortex-fast-v1")
    
    # 4. Convert Balanced Model
    print("\n[4/6] Registering BALANCED Model...")
    run_command(f"{sys.executable} scripts/convert_to_ollama.py --role balanced --adapter models/pdei-exocortex-balanced-v1")
    
    # 5. Validate Fast Model
    print("\n[5/6] Validating FAST Model...")
    run_command(f"{sys.executable} scripts/test_model_accuracy.py --model pdei-jamesthegiblet-fast-v1 --baseline qwen2.5-coder:1.5b")

    # 6. Validate Balanced Model
    print("\n[6/6] Validating BALANCED Model...")
    run_command(f"{sys.executable} scripts/test_model_accuracy.py --model pdei-jamesthegiblet-balanced-v1 --baseline qwen2.5-coder:3b")
    
    print("\n✅ Suite Complete! Both models are ready and validated.")

if __name__ == "__main__":
    main()