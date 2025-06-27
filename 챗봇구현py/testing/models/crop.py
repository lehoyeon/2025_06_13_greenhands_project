# models/crop.py
from pydantic import BaseModel
from typing import Optional, List

class CropRecommendationRequest(BaseModel):
    harvest: str
    environment: str

class CropGuideRequest(BaseModel):
    crop_name: str