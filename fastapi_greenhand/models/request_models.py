# models/request_models.py
from pydantic import BaseModel
from typing import Optional, List

class PlantDiagnosisRequest(BaseModel):
    image_base64: str
    mime_type: str
    prompt: str
    user_id: int

class PlantDiagnosisResponse(BaseModel):
    diagnosis_result: str
    diagnosis_details: str
    severity: str
    plant_name: str
    image_url: Optional[str] = None

class CropRecommendationRequest(BaseModel):
    harvest: str
    environment: str

class CropGuideRequest(BaseModel):
    crop_name: str