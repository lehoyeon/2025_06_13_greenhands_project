# routers/crop_router.py 파일

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from models.request_models import (
    CropRecommendationRequest,
    CropGuideRequest,
    AddUserCropRequest,
    DeleteUserCropRequest,
    ActivateUserCropRequest,
    UserCropResponse,
    RecommendedCropResponse,
    HarvestCropRequest,
    ChecklistItemUpdateRequest,
    ChecklistItemResponse,
    UserCropProgressUpdate
)
from services.ai_service import get_gemini_crop_recommendation, get_gemini_crop_guide
from database import (
    get_db,
    add_user_crop_to_db,
    activate_user_crop_in_db,
    get_user_crops,
    delete_user_crop,
    delete_all_user_crops,
    harvest_user_crop_to_db,
    get_harvested_crops,
    update_checklist_item_status,
    get_user_checklist_items,
    Session,
    UserChecklistItem,
    UserCropNew
)
from knowledge_base import agricultural_knowledge_base, get_crop_by_id
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any, Optional

# SQLAlchemy 쿼리를 위한 임포트는 필요 없음 (db.query 방식으로 처리)


router = APIRouter()

@router.post("/crops/recommend-crop", response_model=List[RecommendedCropResponse])
async def recommend_crop_endpoint(data: CropRecommendationRequest):
    """
    재배 기간, 재배 장소, 지역에 따라 작물을 추천합니다.
    """
    try:
        crops_from_ai_and_kb: List[Dict[str, Any]] = await get_gemini_crop_recommendation(
            environment=data.environment,
            duration=data.duration,
            region=data.region
        )
        if not crops_from_ai_and_kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="선택하신 조건에 맞는 작물이 없습니다.")

        return crops_from_ai_and_kb
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in recommend_crop_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 추천 중 오류 발생: {e}")

@router.post("/crops/crop-guide")
async def crop_guide_endpoint(data: CropGuideRequest):
    """
    특정 작물 ID와 성장 단계에 대한 재배 가이드를 반환합니다.
    """
    try:
        crop_data = get_crop_by_id(data.crop_id)
        if not crop_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"작물 ID '{data.crop_id}'에 대한 정보를 찾을 수 없습니다.")

        detailed_guides_by_stage = crop_data.get("detailed_guides_by_stage")

        requested_stage = data.growth_stage

        guide_to_return = None
        if detailed_guides_by_stage and requested_stage and requested_stage in detailed_guides_by_stage:
            guide_to_return = detailed_guides_by_stage[requested_stage]
            logging.info(f"Returning specific guide for {data.crop_id} at stage: {requested_stage}")
        else:
            default_stage_guide = None
            if detailed_guides_by_stage:
                default_stage_guide = detailed_guides_by_stage.get("파종")

            if default_stage_guide:
                guide_to_return = default_stage_guide
                logging.warning(f"Requested stage '{requested_stage}' not found for {data.crop_id} or not provided. Returning '파종' guide.")
            elif detailed_guides_by_stage:
                first_stage_key = next(iter(detailed_guides_by_stage), None)
                if first_stage_key:
                    guide_to_return = detailed_guides_by_stage[first_stage_key]
                    logging.warning(f"No specific stage or '파종' guide. Returning first available stage '{first_stage_key}'.")
                else:
                    guide_to_return = {"title": "재배 가이드", "guide_text": ["아직 준비된 상세 가이드가 없습니다."]}
            else:
                guide_to_return = {"title": "재배 가이드", "guide_text": ["아직 준비된 상세 가이드가 없습니다."]}
                logging.warning(f"No staged guide for {data.crop_id}. Returning default empty guide.")

        return {"detailed_guide": guide_to_return}

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in crop_guide_endpoint: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 재배 가이드 생성 중 오류 발생: {e}")

@router.get("/crops/crop-info/{crop_id}", response_model=RecommendedCropResponse)
async def get_crop_info_endpoint(crop_id: str):
    """
    특정 작물 ID에 대한 knowledge_base의 모든 정보를 반환합니다.
    """
    crop_data = get_crop_by_id(crop_id)
    if not crop_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"작물 ID '{crop_id}'에 대한 정보를 찾을 수 없습니다.")

    import copy
    response_data = copy.deepcopy(crop_data)
    if "detailed_guides_by_stage" in response_data:
        del response_data["detailed_guides_by_stage"]
    if "detailed_guide" in response_data:
        del response_data["detailed_guide"]

    return RecommendedCropResponse(**response_data)


# === 사용자 작물(재배 리스트) 관련 엔드포인트 ===

@router.post("/crops/user-crops/add")
async def add_user_crop_endpoint(
    data: AddUserCropRequest,
    db: Session = Depends(get_db)
):
    """
    사용자의 재배 리스트에 작물을 추가합니다. (기본적으로 is_main_crop=False)
    """
    try:
        added_user_crop = add_user_crop_to_db(
            db,
            data.user_id,
            data.crop_id,
            data.alias,
            is_main=data.is_main_crop,
            planting_method=None
        )
        if not added_user_crop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="작물 ID '{data.crop_id}'에 대한 정보를 찾을 수 없거나 추가에 실패했습니다.")

        return {"message": "작물이 재배 리스트에 성공적으로 추가되었습니다.", "user_crop_id": added_user_crop.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to add user crop: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 추가 중 오류 발생: {e}")

@router.post("/crops/user-crops/activate")
async def activate_user_crop_endpoint(
    data: ActivateUserCropRequest,
    db: Session = Depends(get_db)
):
    """
    사용자의 관심 작물을 나의 농장(메인 재배 작물)으로 활성화합니다.
    user_crop_db_id가 있으면 기존 레코드를 업데이트하고, 없으면 새로 추가합니다.
    """
    try:
        activated_crop = activate_user_crop_in_db(
            db,
            data.user_id,
            data.crop_id,
            data.alias,
            data.user_crop_db_id,
            data.is_main_crop,
            data.planting_method
        )
        if not activated_crop:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="작물을 나의 농장에 등록하는 데 실패했습니다.")

        return {"message": "작물이 성공적으로 등록되었습니다.", "user_crop_id": activated_crop.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to activate user crop: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 활성화 중 오류 발생: {e}")


@router.get("/crops/user-crops/{user_id}", response_model=List[UserCropResponse])
async def get_user_crops_endpoint(
    user_id: int,
    is_main_crop: Optional[bool] = Query(None, description="메인 재배 작물 여부로 필터링"),
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 재배 작물 리스트를 조회합니다. (is_main_crop 여부로 필터링 가능)
    progress_percent는 created_at과 expected_cultivation_days를 기준으로 동적으로 계산됩니다.
    """
    try:
        crops_from_db = get_user_crops(db, user_id=user_id, is_main_crop=is_main_crop)

        transformed_crops = []
        current_time = datetime.now()

        for db_crop in crops_from_db:
            calculated_progress_percent = float(db_crop.progress_percent)
            days_remaining = None

            # print(f"\n--- DEBUG LOG FOR CROP ID: {db_crop.id}, Nickname: {db_crop.nick_name} ---")
            # print(f"    DB stored progress (initial/last updated): {db_crop.progress_percent}")
            # print(f"    created_at: {db_crop.created_at} (Type: {type(db_crop.created_at)})")
            # print(f"    expected_cultivation_days: {db_crop.expected_cultivation_days}")
            # print(f"    current_time: {current_time}")


            if db_crop.expected_cultivation_days and db_crop.created_at:
                time_elapsed_delta = current_time - db_crop.created_at
                time_elapsed_seconds = time_elapsed_delta.total_seconds()

                total_expected_seconds = db_crop.expected_cultivation_days * 24 * 60 * 60

                # print(f"    time_elapsed_seconds (since created_at): {time_elapsed_seconds}")
                # print(f"    total_expected_seconds: {total_expected_seconds}")


                if time_elapsed_seconds >= 0 and total_expected_seconds > 0:
                    time_based_additional_progress = (time_elapsed_seconds / total_expected_seconds) * 100.0
                    calculated_progress_percent = float(db_crop.progress_percent) + time_based_additional_progress
                    days_remaining = max(0, round(db_crop.expected_cultivation_days * (1 - calculated_progress_percent / 100.0)))

                else:
                    days_remaining = None
            else:
                days_remaining = None

            calculated_progress_percent = max(0.0, min(100.0, calculated_progress_percent))

            # print(f"    Calculated final progress: {calculated_progress_percent}")
            # print(f"    Calculated days remaining: {days_remaining}")
            # print(f"--------------------------------------------------")

            display_growth_stage = db_crop.growth_stage # 여기서 초기화
            if calculated_progress_percent >= 95 and display_growth_stage not in ["수확", "DIED", "HARVESTED"]:
                display_growth_stage = "수확"
            elif calculated_progress_percent >= 75 and display_growth_stage not in ["결실", "수확", "DIED", "HARVESTED"]:
                display_growth_stage = "결실"
            elif calculated_progress_percent >= 50 and display_growth_stage not in ["개화", "결실", "수확", "DIED", "HARVESTED"]:
                display_growth_stage = "개화"
            elif calculated_progress_percent >= 25 and display_growth_stage not in ["성장", "개화", "결실", "수확", "DIED", "HARVESTED"]:
                display_growth_stage = "성장"
            elif calculated_progress_percent >= 5 and display_growth_stage not in ["새싹", "성장", "개화", "결실", "수확", "DIED", "HARVESTED"]:
                display_growth_stage = "새싹"

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

                growth_stage=display_growth_stage,
                progress_percent=calculated_progress_percent,
                last_photo_uploaded_at=db_crop.last_photo_uploaded_at.isoformat() if db_crop.last_photo_uploaded_at else None,
                growth_stage_start_date=db_crop.growth_stage_start_date.isoformat() if db_crop.growth_stage_start_date else None,
                expected_cultivation_days=db_crop.expected_cultivation_days,
                days_remaining=days_remaining,

                care_instruction=parsed_care_instruction,
                other_notes=db_crop.other_notes,
                crop_status=db_crop.crop_status,
                created_at=db_crop.created_at.isoformat(),
                updated_at=db_crop.updated_at.isoformat(),
                is_main_crop=db_crop.is_main_crop
            ))
        return transformed_crops
    except Exception as e:
        logging.error(f"Failed to retrieve user crops: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 조회 중 오류 발생: {e}")


@router.post("/crops/harvest/{user_id}/{user_crop_id}")
async def harvest_crop_endpoint(
    user_id: int = Path(...),
    user_crop_id: int = Path(...),
    data: HarvestCropRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    특정 작물을 수확 완료 처리하여 Harvested 테이블로 이동시킵니다.
    """
    try:
        success = harvest_user_crop_to_db(db, user_id, user_crop_id, yield_info=data.yield_info)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 작물을 찾거나 수확 완료 처리할 수 없습니다.")
        return {"message": "작물이 성공적으로 수확 완료 처리되어 보관함으로 이동했습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to harvest user crop: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 수확 중 오류 발생: {e}")

@router.get("/crops/harvested-crops/{user_id}", response_model=List[UserCropResponse])
async def get_harvested_crops_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 수확된 작물 리스트를 조회합니다.
    """
    try:
        harvested_crops_from_db = get_harvested_crops(db, user_id=user_id)

        transformed_harvested_crops = []
        for db_crop in harvested_crops_from_db:
            parsed_care_instruction = {}
            if db_crop.care_instruction:
                try:
                    parsed_care_instruction = json.loads(db_crop.care_instruction)
                except json.JSONDecodeError:
                    parsed_care_instruction = {"content": db_crop.care_instruction}

            # ⭐⭐ knowledge_base에서 suitable_regions 정보 가져오기 ⭐⭐
            crop_kb_data = get_crop_by_id(db_crop.crop_id_from_kb)
            suitable_regions_list = crop_kb_data.get("suitable_regions") if crop_kb_data else None

            transformed_harvested_crops.append(UserCropResponse(
                id=db_crop.id,
                user_id=db_crop.user_id,
                crop_id_from_kb=db_crop.crop_id_from_kb,
                crop_name=db_crop.crop_name,
                nick_name=db_crop.nick_name if db_crop.nick_name is not None else "",
                environment=db_crop.environment,
                difficulty=db_crop.difficulty,
                pot_size=db_crop.pot_size,
                water_amount=db_crop.water_amount,
                soil_type=db_crop.soil_type,
                pest_control_info=db_crop.pest_control_info,
                thumbnail_image=db_crop.thumbnail_image,
                progress_percent=float(db_crop.progress_percent),
                last_photo_uploaded_at=db_crop.last_photo_uploaded_at.isoformat() if db_crop.last_photo_uploaded_at else None,
                growth_stage_start_date=db_crop.growth_stage_start_date.isoformat() if db_crop.growth_stage_start_date else None,
                expected_cultivation_days=db_crop.expected_cultivation_days,
                days_remaining=0,
                care_instruction=parsed_care_instruction,
                other_notes=db_crop.other_notes,
                crop_status="HARVESTED",
                created_at=db_crop.created_at.isoformat(),
                updated_at=db_crop.updated_at.isoformat(),
                harvested_at=db_crop.harvested_at.isoformat() if db_crop.harvested_at else None,
                is_main_crop=False,
                suitable_regions=suitable_regions_list # ⭐ DTO에 suitable_regions 값 추가 ⭐
            ))
        return transformed_harvested_crops
    except Exception as e:
        logging.error(f"Failed to retrieve harvested crops: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"수확된 작물 조회 중 오류 발생: {type(e).__name__}: {e}")

@router.delete("/crops/user-crops/{user_id}/{user_crop_id}")
async def delete_user_crop_endpoint(
    user_id: int,
    user_crop_id: int,
    db: Session = Depends(get_db)
):
    """
    사용자의 재배 리스트에서 특정 작물을 삭제합니다.
    """
    try:
        success = delete_user_crop(db, user_id, user_crop_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 작물을 찾거나 삭제할 수 없습니다.")
        return {"message": "작물이 재배 리스트에서 성공적으로 삭제되었습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to delete user crop: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"작물 삭제 중 오류 발생: {e}")

@router.delete("/crops/user-crops/all/{user_id}")
async def delete_all_user_crops_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    사용자의 모든 재배 작물을 삭제합니다.
    """
    try:
        success = delete_all_user_crops(db, user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 사용자의 작물을 찾을 수 없습니다.")
        return {"message": "모든 재배 작물이 성공적으로 삭제되었습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Failed to delete all user crops: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"모든 작물 삭제 중 오류 발생: {e}")

# ⭐⭐⭐ 새로 추가: UserCropNew의 진행률 업데이트 엔드포인트 ⭐⭐⭐
@router.patch("/crops/user-crops/{user_crop_id}", response_model=UserCropResponse)
async def update_user_crop_progress(
    user_crop_id: int,
    request: UserCropProgressUpdate,
    db: Session = Depends(get_db)
):
    try:
        user_crop = db.query(UserCropNew).filter(UserCropNew.id == user_crop_id).first()
        if not user_crop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="작물을 찾을 수 없습니다.")

        user_crop.progress_percent = request.progress_percent
        user_crop.updated_at = datetime.now() # 업데이트 시간 갱신

        db.add(user_crop)
        db.commit()
        db.refresh(user_crop)

        # UserCropResponse DTO로 변환하여 반환
        parsed_care_instruction = {}
        if user_crop.care_instruction:
            try:
                parsed_care_instruction = json.loads(user_crop.care_instruction)
            except json.JSONDecodeError:
                parsed_care_instruction = {"content": user_crop.care_instruction}

        return UserCropResponse(
            id=user_crop.id,
            user_id=user_crop.user_id,
            crop_id_from_kb=user_crop.crop_id_from_kb,
            crop_name=user_crop.crop_name,
            nick_name=user_crop.nick_name,
            environment=user_crop.environment,
            difficulty=user_crop.difficulty,
            pot_size=user_crop.pot_size,
            water_amount=user_crop.water_amount,
            soil_type=user_crop.soil_type,
            pest_control_info=user_crop.pest_control_info,
            thumbnail_image=user_crop.thumbnail_image,
            growth_stage=user_crop.growth_stage,
            progress_percent=float(user_crop.progress_percent),
            last_photo_uploaded_at=user_crop.last_photo_uploaded_at.isoformat() if user_crop.last_photo_uploaded_at else None,
            growth_stage_start_date=user_crop.growth_stage_start_date.isoformat() if user_crop.growth_stage_start_date else None,
            expected_cultivation_days=user_crop.expected_cultivation_days,
            days_remaining=0,
            care_instruction=parsed_care_instruction,
            other_notes=user_crop.other_notes,
            crop_status=user_crop.crop_status,
            created_at=user_crop.created_at.isoformat(),
            updated_at=user_crop.updated_at.isoformat(),
            is_main_crop=user_crop.is_main_crop,
            harvested_at=None,
            suitable_regions=None
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"진행률 업데이트 실패: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"진행률 업데이트 중 오류가 발생했습니다.")

# ⭐⭐⭐ 새로 추가: 체크리스트 항목 상태 업데이트 엔드포인트 ⭐⭐⭐
@router.post("/user-crops/checklist/update", response_model=ChecklistItemResponse)
async def update_checklist_item(
    request: ChecklistItemUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        updated_item = update_checklist_item_status(
            db,
            request.user_id,
            request.user_crop_id,
            request.item_id,
            request.is_completed
        )
        if not updated_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="체크리스트 항목을 찾을 수 없거나 업데이트에 실패했습니다.")

        return ChecklistItemResponse(
            id=updated_item.id,
            user_id=updated_item.user_id,
            user_crop_id=updated_item.user_crop_id,
            item_id=updated_item.item_id,
            is_completed=updated_item.is_completed,
            completed_at=updated_item.completed_at.isoformat() if updated_item.completed_at else None,
            created_at=updated_item.created_at.isoformat(),
            updated_at=updated_item.updated_at.isoformat()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"체크리스트 항목 업데이트 실패: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"체크리스트 항목 업데이트 중 오류가 발생했습니다.")

# ⭐⭐⭐ 새로 추가: 특정 작물의 체크리스트 항목 상태 조회 엔드포인트 ⭐⭐⭐
@router.get("/user-crops/{user_id}/{user_crop_id}/checklist", response_model=List[ChecklistItemResponse])
async def get_user_crop_checklist(user_id: int, user_crop_id: int, db: Session = Depends(get_db)):
    """
    사용자 작물의 체크리스트 항목을 가져옵니다.
    """
    try:
        items = db.query(UserChecklistItem).filter(
            UserChecklistItem.user_id == user_id,
            UserChecklistItem.user_crop_id == user_crop_id
        ).all()
        return [
            ChecklistItemResponse(
                id=item.id,
                user_id=item.user_id,
                user_crop_id=item.user_crop_id,
                item_id=item.item_id,
                is_completed=item.is_completed,
                completed_at=item.completed_at.isoformat() if item.completed_at else None,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat()
            ) for item in items
        ]
    except Exception as e:
        logging.error(f"체크리스트 항목 조회 실패: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"체크리스트 항목 조회 중 오류가 발생했습니다.")