import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import PredictRequest, PredictResponse
from app.inference import load_model, predict_single

logger = logging.getLogger("app.main")

# Resolve template and static directories
APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

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

# Mount static files
app.mount("/static", StaticFiles(directory=str(APP_DIR / "/static" if (APP_DIR / "/static").exists() else APP_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    from app.preprocessing import CATEGORIES
    return templates.TemplateResponse("index.html", {
        "request": request,
        "categories": CATEGORIES,
        "mode": "auto",
        "category": "Social Media",
        "include_data_safety": False
    })

@app.post("/analyze", response_class=HTMLResponse)
def analyze(
    request: Request,
    mode: str = Form(...),
    category: str = Form(...),
    app_id: str = Form(None),
    include_data_safety: str = Form(None),  # Form checkboxes send "true" or are omitted
    permission: str = Form(None)
):
    from app.preprocessing import CATEGORIES, normalize_permission, get_app_permissions_and_data_safety
    
    results = []
    error = None
    data_safety_text = None
    use_data_safety = (include_data_safety == "true" or include_data_safety == "on")

    try:
        if mode == "auto":
            if not app_id:
                raise ValueError("App ID is required for auto-scrape mode.")
            
            # Scrape Play Store
            raw_perms, data_safety_text = get_app_permissions_and_data_safety(app_id.strip())
            if not raw_perms:
                # If scraping returns empty, data_safety_text contains the error message
                raise ValueError(f"No permissions could be scraped for App ID '{app_id}'. Detail: {data_safety_text}")
            
            # Predict for each scraped permission
            seen = set()
            for raw_perm in raw_perms:
                canon_perm = normalize_permission(raw_perm)
                # Deduplicate canonical permissions to keep the results clean
                if canon_perm in seen:
                    continue
                seen.add(canon_perm)
                
                # Perform classification
                pred = predict_single(
                    permission=canon_perm,
                    category=category,
                    data_safety_info=data_safety_text if use_data_safety else ""
                )
                results.append({
                    "raw_permission": raw_perm,
                    "canonical_permission": canon_perm,
                    "probability": pred.probability,
                    "label": "Justified" if pred.risk_class == 1 else "Unjustified"
                })
        else:
            if not permission:
                raise ValueError("Permission string is required for manual input mode.")
            
            canon_perm = normalize_permission(permission)
            pred = predict_single(
                permission=canon_perm,
                category=category
            )
            results.append({
                "raw_permission": permission,
                "canonical_permission": canon_perm,
                "probability": pred.probability,
                "label": "Justified" if pred.risk_class == 1 else "Unjustified"
            })
            
    except Exception as e:
        logger.exception("Analysis execution failed.")
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "categories": CATEGORIES,
        "mode": mode,
        "category": category,
        "app_id": app_id,
        "include_data_safety": use_data_safety,
        "permission": permission,
        "results": results,
        "data_safety_text": data_safety_text if use_data_safety else None,
        "error": error
    })

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    try:
        logger.info(f"Received API prediction request for permission='{request.permission}' and category='{request.category}'")
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
