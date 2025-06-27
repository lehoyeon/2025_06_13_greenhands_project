# models/chat.py
from pydantic import BaseModel

class PlantDiagnosisRequest(BaseModel):
    image_base64: str
    mime_type: str
    prompt: str
    user_id: int