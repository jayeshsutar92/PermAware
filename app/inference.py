import logging
import torch
from transformers import AutoTokenizer, BertForSequenceClassification
from app.config import MODEL_DIR
from app.schemas import PredictResponse

logger = logging.getLogger("app.inference")

# Global variables for model and tokenizer
tokenizer = None
model = None
device = None

def load_model():
    global tokenizer, model, device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Target inference device: {device}")

    # Check if model files exist; if not, run the training pipeline
    if not (MODEL_DIR / "config.json").exists() or not (MODEL_DIR / "model.safetensors").exists():
        logger.warning(f"Model files not found at {MODEL_DIR}. Running training workflow first...")
        from app.train import run_training
        run_training()

    logger.info(f"Loading tokenizer from {MODEL_DIR}")
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), use_fast=True)
    logger.info(f"Loading model from {MODEL_DIR}")
    model = BertForSequenceClassification.from_pretrained(str(MODEL_DIR), num_labels=1)
    model.to(device)
    model.eval()
    logger.info("Model and tokenizer loaded successfully.")

def predict_single(permission: str, category: str, data_safety_info: str = "", threshold: float = 0.5) -> PredictResponse:
    global tokenizer, model, device
    if model is None or tokenizer is None:
        raise RuntimeError("Model is not loaded. Please call load_model() at startup.")

    # Reusing the notebook's preprocessing logic exactly
    text = f"Permission: {permission} | Category: {category}"
    if data_safety_info:
        text = text + " | Data Safety: " + data_safety_info

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=128,
        return_token_type_ids=True
    ).to(device)

    with torch.no_grad():
        logits = model(**inputs).logits.view(-1)
        logit = logits.cpu().item()
        prob = float(torch.sigmoid(torch.tensor(logit)).item())
        
        # Determine predicted class based on threshold
        risk_class = 1 if prob >= threshold else 0
        confidence = prob if risk_class == 1 else 1.0 - prob

    return PredictResponse(
        risk_class=risk_class,
        confidence=confidence,
        probability=prob
    )
