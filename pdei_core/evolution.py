import asyncio
import sys
from pathlib import Path

def check_evolution_trigger(personality: dict) -> bool:
    """
    Checks metrics and performs evolution update if threshold met.
    Returns True if evolution occurred.
    """
    forge = personality.get("forge_theory", {})
    metrics = forge.get("evolution_metrics", {})
    
    current = metrics.get("data_points_collected", 0)
    threshold = metrics.get("retrain_threshold", 100)
    
    if forge.get("enabled") and current >= threshold:
        # Evolution Triggered
        metrics["data_points_collected"] = 0
        metrics["generation"] = metrics.get("generation", 1) + 1
        return True
    return False

async def evolution_watchdog(buddai_provider, interval=10):
    """
    Periodically checks if the AI has learned enough to trigger a retraining cycle.
    buddai_provider: A callable that returns the current BuddAI instance or None.
    """
    print("🧬 Evolution Watchdog Active")
    while True:
        try:
            buddai = buddai_provider()
            if buddai:
                if check_evolution_trigger(buddai.personality):
                    metrics = buddai.personality["forge_theory"]["evolution_metrics"]
                    print(f"🧬 EVOLUTION THRESHOLD REACHED")
                    print("🚀 Triggering LLM Retraining Sequence...")
                    
                    # Locate the script relative to this file
                    root_dir = Path(__file__).parent.parent
                    script_path = root_dir / "scripts" / "retrain_model.py"
                    
                    if script_path.exists():
                        # Run asynchronously to avoid blocking the main executive loop
                        proc = await asyncio.create_subprocess_exec(
                            sys.executable, str(script_path),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        
                        if proc.returncode == 0:
                            print(f"✅ Retraining Output:\n{stdout.decode().strip()}")
                        else:
                            print(f"❌ Retraining Failed:\n{stderr.decode().strip()}")
                    else:
                        print(f"⚠️  Retraining script missing: {script_path}")
                        print("   (Create scripts/retrain_model.py to enable actual fine-tuning)")

                    print(f"✨ Evolution Complete. Now at Generation {metrics['generation']}")
        except Exception as e:
            print(f"⚠️ Watchdog Error: {e}")
        
        await asyncio.sleep(interval)