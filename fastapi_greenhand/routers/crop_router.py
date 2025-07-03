# routers/crop_router.py
import logging
from fastapi import APIRouter, HTTPException, Depends
from models.request_models import (
    CropRecommendationRequest,
    CropGuideRequest,
    AddUserCropRequest,
    DeleteUserCropRequest,
    UserCropResponse,
    RecommendedCropResponse
)
from services.ai_service import get_gemini_crop_recommendation, get_gemini_crop_guide
from database import get_db, add_user_crop, get_user_crops, delete_user_crop, delete_all_user_crops, Session
from knowledge_base import get_crop_by_id
import json
from typing import List, Dict, Any

router = APIRouter()

# --- 이 부분이 중요합니다. /crops/ 경로를 추가합니다. ---

@router.post("/crops/recommend-crop", response_model=List[RecommendedCropResponse]) # /crops/ 추가
async def recommend_crop_endpoint(data: CropRecommendationRequest):
    """
    재배 기간, 재배 장소, 지역에 따라 작물을 추천합니다.
    """
    try:
        crops_from_kb: List[Dict[str, Any]] = await get_gemini_crop_recommendation(
            environment=data.environment,
            duration=data.duration,
            region=data.region
        )
        if not crops_from_kb:
            raise HTTPException(status_code=404, detail="선택하신 조건에 맞는 작물이 없습니다.")
        
        return crops_from_kb 
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in recommend_crop_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"작물 추천 중 오류 발생: {e}")

@router.post("/crops/crop-guide") # /crops/ 추가
async def crop_guide_endpoint(data: CropGuideRequest):
    """
    특정 작물 ID에 대한 재배 가이드를 생성합니다.
    """
    try:
        guide_data = await get_gemini_crop_guide(data.crop_id)
        if not guide_data:
            raise HTTPException(status_code=404, detail=f"작물 ID '{data.crop_id}'에 대한 가이드를 찾을 수 없습니다.")
        return {"detailed_guide": guide_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in crop_guide_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"작물 재배 가이드 생성 중 오류 발생: {e}")

# === 사용자 작물(재배 리스트) 관련 엔드포인트 ===

@router.post("/crops/user-crops/add") # /crops/ 추가
async def add_user_crop_endpoint(
    data: AddUserCropRequest, 
    db: Session = Depends(get_db)
):
    try:
        crop_data_from_kb = get_crop_by_id(data.crop_id) 
        if not crop_data_from_kb:
            raise HTTPException(status_code=404, detail=f"작물 ID '{data.crop_id}'에 대한 정보를 찾을 수 없습니다.")
        
        added_user_crop = add_user_crop(db, data.user_id, crop_data_from_kb, data.alias)
        return {"message": "작물이 재배 리스트에 성공적으로 추가되었습니다.", "user_crop_id": added_user_crop.id}
    except Exception as e:
        logging.error(f"Failed to add user crop: {e}")
        raise HTTPException(status_code=500, detail=f"작물 추가 중 오류 발생: {e}")

@router.get("/crops/user-crops/{user_id}", response_model=List[UserCropResponse]) # /crops/ 추가
async def get_user_crops_endpoint(
    user_id: int, 
    db: Session = Depends(get_db)
):
    try:
        crops_from_db = get_user_crops(db, user_id)
        
        transformed_crops = []
        for db_crop in crops_from_db:
            parsed_care_instruction = {}
            if db_crop.care_instruction:
                try:
                    parsed_care_instruction = json.loads(db_crop.care_instruction)
                except json.JSONDecodeError:
                    parsed_care_instruction = {"content": db_crop.care_instruction} 
            
            transformed_crops.append(UserCropResponse(
                id=db_crop.id,
                user_id=db_crop.user_id,
                crop_id_from_kb=db_crop.crop_id_from_kb,
                crop_name=db_crop.crop_name,
                nick_name=db_crop.nick_name,
                
                environment=db_crop.environment,
                difficulty=db_crop.difficulty,
                pot_size=db_crop.pot_size,
                water_amount=db_crop.water_amount,
                soil_type=db_crop.soil_type,
                pest_control_info=db_crop.pest_control_info,
                thumbnail_image=db_crop.thumbnail_image,

                growth_stage=db_crop.growth_stage,
                care_instruction=parsed_care_instruction,
                other_notes=db_crop.other_notes,
                crop_status=db_crop.crop_status,
                created_at=db_crop.created_at.isoformat(),
                updated_at=db_crop.updated_at.isoformat(),
            ))
        return transformed_crops
    except Exception as e:
        logging.error(f"Failed to retrieve user crops: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 작물 조회 중 오류 발생: {e}")

@router.delete("/crops/user-crops/{user_id}/{user_crop_id}") # /crops/ 추가
async def delete_user_crop_endpoint(
    user_id: int, 
    user_crop_id: int, 
    db: Session = Depends(get_db)
):
    try:
        success = delete_user_crop(db, user_id, user_crop_id)
        if not success:
            raise HTTPException(status_code=404, detail="해당 작물을 찾거나 삭제할 수 없습니다.")
        return {"message": "작물이 재배 리스트에서 성공적으로 삭제되었습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to delete user crop: {e}")
        raise HTTPException(status_code=500, detail=f"작물 삭제 중 오류 발생: {e}")

@router.delete("/crops/user-crops/all/{user_id}") # /crops/ 추가
async def delete_all_user_crops_endpoint(
    user_id: int, 
    db: Session = Depends(get_db)
):
    try:
        success = delete_all_user_crops(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="해당 사용자의 작물을 찾을 수 없습니다.")
        return {"message": "모든 재배 작물이 성공적으로 삭제되었습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to delete all user crops: {e}")
        raise HTTPException(status_code=500, detail=f"모든 작물 삭제 중 오류 발생: {e}")