import argparse
import random
import json
import os
import sys

def split_dataset(input_file, train_file, val_file, ratio):
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    print(f"🔍 Reading {input_file}...")
    
    valid_lines = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line.startswith('//') or line.startswith('#'): continue
                try:
                    json.loads(line)
                    valid_lines.append(line)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

    total = len(valid_lines)
    print(f"📊 Total valid examples: {total}")
    
    if total == 0:
        print("⚠️  No valid data found to split.")
        sys.exit(0)

    # Shuffle for random distribution
    random.seed(42) # Reproducibility
    random.shuffle(valid_lines)

    split_idx = int(total * ratio)
    train_data = valid_lines[:split_idx]
    val_data = valid_lines[split_idx:]

    print(f"✂️  Splitting with ratio {ratio}:")
    print(f"   - Training: {len(train_data)} examples")
    print(f"   - Validation: {len(val_data)} examples")

    try:
        with open(train_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(train_data) + '\n')
        
        with open(val_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(val_data) + '\n')
            
        print(f"✅ Saved to {train_file} and {val_file}")
    except Exception as e:
        print(f"❌ Error writing output files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split JSONL dataset into training and validation sets")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--train", required=True, help="Output training JSONL file")
    parser.add_argument("--val", required=True, help="Output validation JSONL file")
    parser.add_argument("--ratio", type=float, default=0.8, help="Training ratio (e.g. 0.8 for 80%)")
    
    args = parser.parse_args()
    
    split_dataset(args.input, args.train, args.val, args.ratio)