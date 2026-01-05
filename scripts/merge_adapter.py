import argparse
import os
import sys
import logging
import traceback
import gc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDEI-Merger")

def merge_model(base_model_id, adapter_path, output_dir):
    """
    Merges a LoRA adapter into a base model and saves the result.
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError:
        logger.error("❌ Missing ML libraries.")
        logger.info("Please install: pip install torch transformers peft")
        return False

    logger.info(f"🔄 Loading base model: {base_model_id}")
    try:
        # Load base model
        # Use float16 if GPU is available for memory efficiency, else float32 for CPU
        device_map = "auto" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            dtype=dtype,
            device_map=device_map,
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    except Exception as e:
        logger.error(f"❌ Error loading base model: {e}")
        return False

    logger.info(f"🔄 Loading adapter from: {adapter_path}")
    try:
        # Load adapter and attach to base model
        model = PeftModel.from_pretrained(base_model, adapter_path)
    except Exception as e:
        logger.error(f"❌ Error loading adapter: {e}")
        return False

    logger.info("🔄 Merging adapter weights into base model...")
    try:
        # Merge weights and unload adapter to create a standalone model
        model = model.merge_and_unload()
        
        # Memory optimization: Cast to float16 on CPU to prevent MemoryError during save
        if model.device.type == 'cpu':
            logger.info("📉 Casting model to float16 to save memory...")
            model = model.half()
            
        gc.collect()
    except Exception as e:
        logger.error(f"❌ Error during merge: {e}")
        return False

    logger.info(f"💾 Saving merged model to: {output_dir}")
    try:
        model.save_pretrained(output_dir, safe_serialization=True, max_shard_size="1GB")
        tokenizer.save_pretrained(output_dir)
        logger.info("✅ Merge complete.")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving model: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base", required=True, help="Base model ID or path (e.g., Qwen/Qwen2.5-Coder-1.5B)")
    parser.add_argument("--adapter", required=True, help="Path to LoRA adapter directory")
    parser.add_argument("--output", required=True, help="Output directory for merged model")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.adapter):
        logger.error(f"❌ Adapter path not found: {args.adapter}")
        sys.exit(1)
        
    success = merge_model(args.base, args.adapter, args.output)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()