import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.schemas import PredictRequest, PredictResponse
from app.inference import load_model, predict_single

logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up FastAPI application and loading models...")
    try:
        load_model()
    except Exception as e:
        logger.exception("Critical failure during model loading at startup.")
        raise RuntimeError(f"Startup failed: {e}") from e
    yield
    logger.info("Shutting down FastAPI application...")

app = FastAPI(
    title="PermAware BERT Inference Service",
    description="FastAPI service for context-aware Android permission justification classification.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {
        "status": "healthy",
        "model": "BERT sequence classification",
        "task": "Permission justification classification (0 = Unjustified, 1 = Justified)"
    }

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    try:
        logger.info(f"Received prediction request for permission='{request.permission}' and category='{request.category}'")
        response = predict_single(
            permission=request.permission,
            category=request.category,
            data_safety_info=request.data_safety_info,
            threshold=request.threshold
        )
        return response
    except Exception as e:
        logger.exception("Error during prediction endpoint execution.")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
