import os
import sys
import sqlite3
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDEI-Trainer")

def load_training_data(db_path):
    """Extracts correction pairs from the PDEI memory database."""
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        logger.info("💡 Tip: Run 'python scripts/seed_memory.py' to generate sample training data.")
        return []

    logger.info(f"📦 Loading data from {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch corrections: We want to learn from mistakes
    # Input: Original Code + Context
    # Output: Corrected Code
    cursor.execute("SELECT original_code, corrected_code, context FROM corrections")
    rows = cursor.fetchall()
    conn.close()

    dataset = []
    for orig, fixed, ctx in rows:
        # Format for instruction tuning
        prompt = f"Context: {ctx}\nFix the following code:\n```\n{orig}\n```"
        response = f"```\n{fixed}\n```"
        dataset.append({"prompt": prompt, "completion": response})
    
    logger.info(f"✅ Loaded {len(dataset)} training examples.")
    return dataset

def train_model(data, base_model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0", output_dir="./fine_tuned_adapter"):
    """Runs the QLoRA training loop."""
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
        )
        from trl import SFTTrainer
    except ImportError as e:
        logger.error("❌ Missing AI training libraries.")
        logger.info("Please install: pip install torch transformers peft bitsandbytes trl datasets scipy accelerate")
        return False

    logger.info(f"🔧 Preparing QLoRA training for {base_model_id}...")

    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    tokenizer.pad_token = tokenizer.eos_token

    # 2. Load Base Model (Try 4-bit first, fallback to standard)
    model = None
    if torch.cuda.is_available():
        try:
            logger.info("🎮 GPU detected. Attempting 4-bit quantization...")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
            model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                quantization_config=bnb_config,
                device_map="auto"
            )
            model = prepare_model_for_kbit_training(model)
        except Exception as e:
            logger.warning(f"⚠️  4-bit Quantization failed: {e}")
            logger.info("🔄 Falling back to standard loading...")

    if model is None:
        device_map = "auto" if torch.cuda.is_available() else "cpu"
        logger.info(f"🖥️  Loading model on {device_map.upper()} (Standard Mode)...")
        try:
            model = AutoModelForCausalLM.from_pretrained(base_model_id, device_map=device_map)
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False

    # 3. Configure LoRA (Low-Rank Adaptation)
    peft_config = LoraConfig(
        r=16,       # Rank
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=["q_proj", "v_proj"] # Target attention layers
    )
    model = get_peft_model(model, peft_config)

    # 4. Prepare Dataset
    hf_dataset = Dataset.from_list(data)
    # Pre-format the dataset to avoid SFTTrainer conflict with formatting_func + completion_only_loss
    def format_row(example):
        return {"text": f"### User: {example['prompt']}\n### Assistant: {example['completion']}"}
    hf_dataset = hf_dataset.map(format_row)

    # 5. Training Arguments
    use_gpu = torch.cuda.is_available()
    logger.info(f"⚙️  Training Config: GPU={use_gpu}, FP16={use_gpu}")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=10,
        max_steps=50, # Short run for demonstration/evolution cycles
        optim="paged_adamw_32bit" if use_gpu else "adamw_torch",
        fp16=use_gpu,     # Disable FP16 on CPU
        use_cpu=not use_gpu # Explicitly tell trainer to use CPU if needed
    )

    # 6. Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=hf_dataset,
        peft_config=peft_config,
        args=training_args,
    )

    logger.info("🚀 Starting Training...")
    trainer.train()
    
    logger.info(f"💾 Saving adapter to {output_dir}...")
    trainer.model.save_pretrained(output_dir)
    return True

def main():
    parser = argparse.ArgumentParser(description="P.DE.I Evolution Trainer")
    parser.add_argument("--db", type=str, default="data/db/memory.db", help="Path to memory database")
    parser.add_argument("--model", type=str, default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", help="HuggingFace model ID")
    parser.add_argument("--output", type=str, default="data/models/adapter_v1", help="Output directory for adapter")
    args = parser.parse_args()

    # Resolve paths relative to project root
    root_dir = Path(__file__).parent.parent
    db_path = root_dir / args.db
    output_path = root_dir / args.output

    data = load_training_data(str(db_path))
    
    if not data:
        logger.warning("⚠️  No training data found. Skipping evolution.")
        return

    if len(data) < 10:
        logger.warning(f"⚠️  Insufficient data points ({len(data)}). Recommend at least 10.")
        # Proceeding anyway for testing purposes

    success = train_model(data, base_model_id=args.model, output_dir=str(output_path))
    
    if success:
        print("✅ [Script] Model Updated Successfully.")
    else:
        print("❌ [Script] Training Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()