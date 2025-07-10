# routers/diagnosis_router.py
import logging
from fastapi import APIRouter, HTTPException
from models.request_models import PlantDiagnosisRequest, PlantDiagnosisResponse
from services.ai_service import get_gemini_plant_diagnosis

router = APIRouter()

@router.post("/plant", response_model=PlantDiagnosisResponse)
async def diagnose_plant_with_gemini_endpoint(request: PlantDiagnosisRequest):
    logging.info(f"Request received for /diagnose/plant. user_id={request.user_id}, mime_type={request.mime_type}, prompt='{request.prompt[:50]}...'")

    try:
        diagnosis_data = await get_gemini_plant_diagnosis(
            image_base64=request.image_base64,
            mime_type=request.mime_type,
            prompt=request.prompt
        )
        return PlantDiagnosisResponse(**diagnosis_data)
    except HTTPException as e:
        raise e # Re-raise HTTPExceptions from service layer
    except Exception as e:
        logging.error(f"Unexpected error in diagnose_plant_with_gemini_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"식물 진단 중 오류 발생: {str(e)}. 상세 오류: {type(e).__name__}")