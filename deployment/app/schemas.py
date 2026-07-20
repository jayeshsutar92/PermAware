from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    permission: str = Field(..., description="Permission string to classify (e.g. 'Location', 'Camera')")
    category: str = Field("Social Media", description="Application category (e.g. 'Social Media', 'Gaming')")
    data_safety_info: str = Field("", description="Optional data safety information")
    threshold: float = Field(0.5, description="Classification threshold")

class PredictResponse(BaseModel):
    risk_class: int = Field(..., description="Predicted class (0 for Unjustified, 1 for Justified)")
    confidence: float = Field(..., description="Confidence score (probability of the predicted class)")
    probability: float = Field(..., description="Probability of class 1 (Justified)")
