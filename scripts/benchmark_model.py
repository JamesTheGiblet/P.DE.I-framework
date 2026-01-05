import time
import argparse
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("PDEI-Benchmark")

def benchmark(model_path, prompt="Write a function to calculate Fibonacci numbers.", num_runs=3):
    if not os.path.exists(model_path):
        logger.error(f"Model path not found: {model_path}")
        return

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        logger.error("Missing libraries. Run: pip install torch transformers accelerate")
        return

    logger.info(f"⏳ Loading model from {model_path}...")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            device_map="auto", 
            dtype=dtype
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    logger.info(f"🚀 Starting benchmark on {device.upper()}...")
    print("-" * 50)
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_len = len(inputs['input_ids'][0])
    
    total_tokens = 0
    total_time = 0
    
    # Warmup
    logger.info("🔥 Warming up...")
    model.generate(**inputs, max_new_tokens=10)
    
    for i in range(num_runs):
        logger.info(f"🏃 Run {i+1}/{num_runs}...")
        start_time = time.time()
        
        outputs = model.generate(
            **inputs, 
            max_new_tokens=50, 
            do_sample=True, 
            temperature=0.7
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate tokens generated (excluding prompt)
        new_tokens = len(outputs[0]) - input_len
        
        total_tokens += new_tokens
        total_time += duration
        
        tps = new_tokens / duration
        print(f"   Run {i+1}: {new_tokens} tokens in {duration:.2f}s ({tps:.2f} tokens/sec)")

    avg_tps = total_tokens / total_time
    print("-" * 50)
    print(f"📊 Average Speed: {avg_tps:.2f} tokens/sec")
    print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark P.DE.I model inference speed")
    parser.add_argument("--model", default="models/pdei-tinyllama-v1-merged", help="Path to merged model directory")
    parser.add_argument("--prompt", default="Write a function to fade an LED.", help="Prompt to use for generation")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs")
    
    args = parser.parse_args()
    benchmark(args.model, args.prompt, args.runs)