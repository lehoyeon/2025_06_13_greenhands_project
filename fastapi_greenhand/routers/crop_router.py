# routers/crop_router.py
import logging
from fastapi import APIRouter, HTTPException
from models.request_models import CropRecommendationRequest, CropGuideRequest
from services.ai_service import get_gemini_crop_recommendation, get_gemini_crop_guide

router = APIRouter()

@router.post("/recommend-crop")
async def recommend_crop_endpoint(data: CropRecommendationRequest):
    """
    수확 희망 시기와 재배 장소에 따라 작물을 추천합니다.
    응답은 JSON 배열 형식으로 작물 정보(이름, 화분 크기, 물의 양, 토양 유형, 난이도)를 반환합니다.
    """
    try:
        crops = await get_gemini_crop_recommendation(data.harvest, data.environment)
        return crops
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in recommend_crop_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"작물 추천 중 오류 발생: {e}")

@router.post("/crop-guide")
async def crop_guide_endpoint(data: CropGuideRequest):
    """
    특정 작물에 대한 재배 가이드를 생성합니다.
    응답은 JSON 배열 형식으로 단계별 가이드를 반환합니다.
    """
    try:
        guide_steps = await get_gemini_crop_guide(data.crop_name)
        return guide_steps
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in crop_guide_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"작물 재배 가이드 생성 중 오류 발생: {e}")