import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.config")

# Project Root Directory
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

# Model directory resolved dynamically
MODEL_DIR = BASE_DIR / "my_model_bce"

logger.info(f"Resolved BASE_DIR: {BASE_DIR}")
logger.info(f"Resolved MODEL_DIR: {MODEL_DIR}")
