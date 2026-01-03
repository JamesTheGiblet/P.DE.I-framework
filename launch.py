#!/usr/bin/env python3
import uvicorn
import sys
import os
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Launcher")

def main():
    # 1. Setup Environment
    parser = argparse.ArgumentParser(description="P.DE.I Server Launcher")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    args = parser.parse_args()

    if args.config:
        os.environ["PDEI_CONFIG"] = str(Path(args.config).absolute())
        logger.info(f"⚙️  Configuration: {os.environ['PDEI_CONFIG']}")

    script_path = Path(__file__).parent.absolute()
    # If script is in domain_configs, root is one level up
    root_dir = script_path.parent if script_path.name == "domain_configs" else script_path
    
    sys.path.insert(0, str(root_dir))
    
    logger.info(f"📂 Framework Root: {root_dir}")
    
    # 2. Check Dependencies (Minimal check)
    try:
        import fastapi
        import pdei_core
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        sys.exit(1)

    # 3. Create Data Directories
    data_dir = root_dir / "data"
    (data_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (data_dir / "db").mkdir(parents=True, exist_ok=True)
    
    # 4. Launch Server
    logger.info("🚀 Initializing P.DE.I Server...")
    # Reload dirs ensures changes in core or configs trigger a restart
    uvicorn.run(
        "pdei_core.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(root_dir / "pdei_core"), str(root_dir / "domain_configs")]
    )

if __name__ == "__main__":
    main()