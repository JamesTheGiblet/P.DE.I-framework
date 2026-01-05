import time
import argparse
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDEI-Benchmark")

def benchmark(model_path: str, prompt: str = "Write a function to fade an LED.", num_runs: int = 3) -> None:
    if num_runs < 1:
        logger.error("Number of runs must be at least 1.")
        return

    if not os.path.exists(model_path):
        logger.warning(f"Model path '{model_path}' not found locally. Attempting to load from Hugging Face Hub...")

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        logger.error("Missing libraries. Run: pip install torch transformers accelerate")
        sys.exit(1)

    logger.info(f"⏳ Loading model from {model_path}...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            device_map="auto", 
            torch_dtype="auto"
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    device = model.device
    logger.info(f"🚀 Starting benchmark on {device}...")
    print("-" * 50)
    
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    input_len = inputs['input_ids'].shape[-1]
    
    total_tokens = 0
    total_time = 0
    
    # Warmup
    logger.info("🔥 Warming up...")
    with torch.no_grad():
        model.generate(**inputs, max_new_tokens=10, pad_token_id=tokenizer.pad_token_id)
    
    for i in range(num_runs):
        logger.info(f"🏃 Run {i+1}/{num_runs}...")
        start_time = time.time()
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=50, 
                do_sample=True, 
                temperature=0.7,
                pad_token_id=tokenizer.pad_token_id
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate tokens generated (excluding prompt)
        new_tokens = len(outputs[0]) - input_len
        
        total_tokens += new_tokens
        total_time += duration
        
        tps = new_tokens / duration
        print(f"   Run {i+1}: {new_tokens} tokens in {duration:.2f}s ({tps:.2f} tokens/sec)")

    if total_time > 0:
        avg_tps = total_tokens / total_time
        print("-" * 50)
        print(f"📊 Average Speed: {avg_tps:.2f} tokens/sec")
        print("-" * 50)
    else:
        logger.warning("Total time was 0, cannot calculate average speed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark P.DE.I model inference speed")
    parser.add_argument("--model", default="models/pdei-tinyllama-v1-merged", help="Path to merged model directory or HF Hub ID")
    parser.add_argument("--prompt", default="Write a function to fade an LED.", help="Prompt to use for generation")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs")
    
    args = parser.parse_args()
    benchmark(args.model, args.prompt, args.runs)