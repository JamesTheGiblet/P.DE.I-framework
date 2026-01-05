"""
scripts/run_inference.py
Directly load and chat with a merged P.DE.I model using Transformers.
"""
import argparse
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("PDEI-Inference")

def chat(model_path):
    if not os.path.exists(model_path):
        logger.error(f"Model path not found: {model_path}")
        return

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except ImportError:
        logger.error("Missing libraries. Run: pip install torch transformers accelerate")
        return

    logger.info(f"⏳ Loading model from {model_path}...")
    
    # Determine device
    device = 0 if torch.cuda.is_available() else -1
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

    # Create generation pipeline
    pipe = pipeline(
        "text-generation", 
        model=model, 
        tokenizer=tokenizer,
        device_map="auto"
    )
    
    logger.info("✅ Model loaded. Type 'exit' to quit.")
    print("-" * 50)
    print(f"🤖 Model: {os.path.basename(model_path)}")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            # Format prompt matching the training data (Alpaca/ChatML style used in retrain_model.py)
            prompt = f"### User: {user_input}\n### Assistant:"
            
            outputs = pipe(
                prompt, 
                max_new_tokens=128, 
                do_sample=True, 
                temperature=0.7,
                top_p=0.9,
                truncation=True
            )
            
            generated_text = outputs[0]['generated_text']
            # Extract just the assistant part
            response = generated_text.split("### Assistant:")[-1].strip()
            print(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Generation Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run inference on merged P.DE.I model")
    parser.add_argument("--model", default="models/pdei-tinyllama-v1-merged", help="Path to merged model directory")
    args = parser.parse_args()
    chat(args.model)
