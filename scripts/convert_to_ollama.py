r"""
C:\Users\gilbe\Documents\GitHub\readme-hub\P.DE.I-framework\scripts\convert_to_ollama.py
P.DE.I Framework - Ollama Model Converter
=========================================

This script automates the creation of custom Ollama models (Modelfiles) based on 
P.DE.I's domain rules and personality settings. It simulates the fine-tuning process 
by injecting rules into the system prompt of a base model.

Key Functions:
1. Modelfile Generation: Creates a Modelfile defining the system prompt and parameters.
2. Rule Injection: Embeds critical Forge Theory rules (Decay, Safety, etc.) into the model context.
3. Model Creation: Invokes `ollama create` to build the local model.

Usage:
    python scripts/convert_to_ollama.py --name <new_model_name> --base <base_model>

Where it fits:
    This script is used to "compile" the learned rules and configuration into a 
    deployable Ollama model artifact.
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path

# Allow importing sibling scripts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import merge_adapter
except ImportError:
    merge_adapter = None

# Mapping roles to Ollama Base Models
OLLAMA_MAP = {
    "fast": "qwen2.5-coder:1.5b",
    "balanced": "qwen2.5-coder:3b"
}

HF_MAP = {
    "qwen2.5-coder:1.5b": "Qwen/Qwen2.5-Coder-1.5B",
    "qwen2.5-coder:3b": "Qwen/Qwen2.5-Coder-3B"
}

def convert(args):
    # Determine Base Model
    base_model = args.base
    if args.role and args.role in OLLAMA_MAP:
        base_model = OLLAMA_MAP[args.role]
        
    # Auto-name if default
    model_name = args.name
    if args.role and model_name == "james-qwen-gilbot-v1":
        model_name = f"pdei-jamesthegiblet-{args.role}-v1"

    print(f"🐳 Creating Ollama Model: {model_name}")
    
    # Optional: Merge Adapter if requested
    if args.merge and args.adapter and os.path.exists(args.adapter):
        if merge_adapter:
            print(f"🔄 Attempting to merge adapter: {args.adapter}")
            # Map Ollama tag to HF ID for merging
            hf_base = HF_MAP.get(base_model, base_model)
            output_dir = os.path.join("models", f"{model_name}-merged")
            output_dir = os.path.abspath(output_dir)
            
            success = merge_adapter.merge_model(hf_base, args.adapter, output_dir)
            if success:
                print(f"✅ Merged model saved to: {output_dir}")
                print("⚠️  NOTE: To use this in Ollama, convert to GGUF via llama.cpp, then update Modelfile FROM.")
        else:
            print("⚠️  Cannot merge: merge_adapter module missing or dependencies (torch, peft) not installed.")
    
    ollama_base = args.ollama_base if args.ollama_base else base_model
    
    # Create Modelfile (System Prompt Injection Strategy)
    modelfile_content = f"FROM {ollama_base}\n"
    
    modelfile_content += 'SYSTEM """\n'
    modelfile_content += "You are P.DE.I (Personal Data-driven Exocortex Intelligence).\n"
    modelfile_content += "You have been fine-tuned on the user's specific domain rules and coding style.\n"
    modelfile_content += "Always prioritize safety, modularity, and Forge Theory compliance.\n"
    modelfile_content += "Provide code solutions directly.\n"
    modelfile_content += "\nDECISION PROTOCOL:\n"
    modelfile_content += "1. Analyze: Is the value going to 0 (Decay) or to a Target (Growth)?\n"
    modelfile_content += "2. Select Formula: Decay = exp(-t/tau), Growth = 1 - exp(-t/tau).\n"
    modelfile_content += "3. Apply Safety: Check timeouts and non-blocking logic.\n"
    modelfile_content += "\nCRITICAL RULES:\n"
    modelfile_content += "1. Decay: Use 'exp(-t/tau)'. Never use positive exponents.\n"
    modelfile_content += "2. Growth: Use '(1 - exp(-t/tau))'.\n"
    modelfile_content += "3. Step Response: Use 'target * (1 - exp(-t/tau))'.\n"
    modelfile_content += "4. Safety: Use 'millis() - lastCommand > SAFETY_TIMEOUT'.\n"
    modelfile_content += "5. Concurrency: Never use blocking 'delay()'.\n"
    modelfile_content += "\nEXAMPLES:\n"
    modelfile_content += "User: Fade LED to off\n"
    modelfile_content += "Assistant: brightness = 255 * exp(-t/tau); // Decay\n\n"
    modelfile_content += "User: Move servo to target\n"
    modelfile_content += "Assistant: pos = target * (1 - exp(-t/tau)); // Growth\n\n"
    modelfile_content += "User: Weapon flipper control\n"
    modelfile_content += "Assistant: angle = target * (1 - exp(-t/tau)); // Step Response\n\n"
    modelfile_content += "User: Wait for 500ms\n"
    modelfile_content += "Assistant: if (millis() - last > 500) { ... } // Non-blocking\n\n"
    modelfile_content += "User: Motor control loop\n"
    modelfile_content += "Assistant: if (millis() - lastCommand > SAFETY_TIMEOUT) { stopMotors(); }\n"
    modelfile_content += '"""\n'
    
    # Parameters for consistent behavior
    modelfile_content += "PARAMETER temperature 0.3\n"
    modelfile_content += "PARAMETER stop \"<|endoftext|>\"\n"
    
    modelfile_path = "Modelfile_custom"
    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(modelfile_content)
        
    print(f"📄 Generated Modelfile:\n{modelfile_content}")
    
    if args.skip_create:
        print(f"⚠️  Skipping 'ollama create'. Run manually: ollama create {model_name} -f {modelfile_path}")
        return

    try:
        print(f"⚡ Running: ollama create {model_name} -f {modelfile_path}")
        subprocess.check_call(["ollama", "create", model_name, "-f", modelfile_path])
        print(f"✅ Model '{model_name}' created successfully!")
        print(f"👉 Try it: ollama run {model_name}")
    except FileNotFoundError:
        print("❌ Error: 'ollama' command not found. Is it installed?")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating model: {e}")
    finally:
        if os.path.exists(modelfile_path):
            os.remove(modelfile_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert fine-tuned adapter to Ollama model")
    parser.add_argument("--role", choices=["fast", "balanced"], help="Preset configuration for Fast or Balanced")
    parser.add_argument("--name", default="james-qwen-gilbot-v1", help="Name for the new Ollama model")
    parser.add_argument("--base", default="qwen2.5-coder:3b", help="Base Ollama model (e.g. qwen2.5-coder:3b)")
    parser.add_argument("--adapter", default="models/james-qwen-gilbot-v1.0", help="Path to adapter directory")
    parser.add_argument("--merge", action="store_true", help="Attempt to merge adapter into base model (requires ML libs)")
    parser.add_argument("--ollama-base", help="Base model for Modelfile FROM (if different from --base)")
    parser.add_argument("--skip-create", action="store_true", help="Skip 'ollama create' command")
    
    args = parser.parse_args()
    convert(args)