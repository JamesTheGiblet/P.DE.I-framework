import json
import sys
import os
from datetime import datetime

def validate_jsonl(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print(f"🔍 Inspecting {file_path}...")
    
    # File Stats (mimic ls -lh)
    stats = os.stat(file_path)
    size = stats.st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: break
        size /= 1024
    mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"📂 Size: {size:.1f} {unit} | 📅 Modified: {mtime}")

    # Content Validation (mimic wc -l + validation)
    valid = 0
    invalid = 0
    comments = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line: continue
                if line.startswith('//') or line.startswith('#'):
                    comments += 1
                    continue
                try:
                    json.loads(line)
                    valid += 1
                except json.JSONDecodeError:
                    print(f"⚠️  Line {i}: Invalid JSON")
                    invalid += 1
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
                
    print(f"📊 Report: {valid} valid lines | {comments} comments | {invalid} errors")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_jsonl(sys.argv[1])
    else:
        print("Usage: python scripts/validate_dataset.py <file_path>")