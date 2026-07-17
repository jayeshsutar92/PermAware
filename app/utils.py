import random
import logging
import numpy as np
import torch

logger = logging.getLogger("app.utils")

def set_seed(seed: int = 42):
    """
    Sets random seed for reproducibility across python, numpy, and torch.
    """
    logger.info(f"Setting random seed: {seed}")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
