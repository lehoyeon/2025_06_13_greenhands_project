# request_models.py 파일

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

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
    image_url: Optional[str] = None # 서버에 저장된 이미지 URL

class CropRecommendationRequest(BaseModel):
    environment: str
    duration: str
    region: str

class CropGuideRequest(BaseModel):
    crop_id: str
    growth_stage: Optional[str] = None # ⭐ 추가: 성장 단계 필드 ⭐

class AddUserCropRequest(BaseModel):
    user_id: int
    crop_id: str # knowledge_base에 정의된 작물의 고유 ID
    alias: Optional[str] = None
    is_main_crop: bool = False # <-- 이 필드를 추가했습니다. (기본값 False)

class DeleteUserCropRequest(BaseModel):
    user_id: int
    user_crop_id: int

class ActivateUserCropRequest(BaseModel):
    user_id: int
    crop_id: str # knowledge_base의 ID
    alias: Optional[str] = None
    user_crop_db_id: Optional[int] = None # 기존 UserCrop의 DB ID
    is_main_crop: bool # ⭐ 추가: is_main_crop 필드 (프론트엔드에서 보냄) ⭐
    planting_method: str # ⭐ 추가: 'seed' 또는 'seedling' (프론트엔드에서 보냄) ⭐

# 추천 작물 반환용 모델 (Gemini AI 응답 구조와 일치)
class RecommendedCropResponse(BaseModel):
    name: str = Field(..., description="작물 한글 이름 (예: '상추')")
    pot_size: str = Field(..., description="권장 화분 크기")
    water_amount: str = Field(..., description="권장 물의 양")
    soil_type: str = Field(..., description="권장 토양 유형")
    difficulty: str = Field(..., description="재배 난이도 (예: '하', '중', '상')")

    id: Optional[str] = Field(None, description="작물 고유 ID (knowledge_base의 ID)")
    cultivation_duration: Optional[str] = Field(None, description="권장 재배 기간")
    cultivation_location: Optional[List[str]] = Field(None, description="권장 재배 장소")
    suitable_regions: Optional[List[str]] = Field(None, description="적합 지역")
    thumbnail_image: Optional[str] = Field(None, description="작물 썸네일 이미지 URL")
    initial_preparations: Optional[List[str]] = Field(None, description="초기 준비물 및 과정")
    pest_control: Optional[str] = Field(None, description="흔한 병충해 및 간단 관리법")
    detailed_guide: Optional[Union[Dict[str, str], List[str]]] = Field(None, description="상세 재배 가이드")
    
    # knowledge_base.py의 watering_frequency_detail 구조를 반영하기 위한 필드 (AI 추천 시 활용될 경우)
    watering_frequency_detail: Optional[Dict[str, Any]] = Field(None, description="물 주는 주기 상세 정보")
    expected_cultivation_days: Optional[int] = Field(None, description="예상 총 재배 일수")


    class Config:
        from_attributes = True # dict에서 Pydantic 모델로 매핑 허용

# 사용자 재배 작물 (DB에서 가져옴) 모델
class UserCropResponse(BaseModel):
    id: int # 데이터베이스 PK
    user_id: int
    crop_id_from_kb: str # knowledge_base의 ID
    crop_name: str
    nick_name: Optional[str] = None
    
    environment: Optional[str] = None 
    difficulty: Optional[str] = None
    pot_size: Optional[str] = None
    water_amount: Optional[str] = None
    soil_type: Optional[str] = None
    pest_control_info: Optional[str] = None
    thumbnail_image: Optional[str] = None

    growth_stage: Optional[str] = None
    progress_percent: float
    last_photo_uploaded_at: Optional[str] = None
    growth_stage_start_date: Optional[str] = None
    expected_cultivation_days: Optional[int] = Field(None, description="예상 총 재배 일수")
    days_remaining: Optional[int] = Field(None, description="수확까지 남은 일수")

    care_instruction: Optional[Any] = None
    other_notes: Optional[str] = None
    crop_status: str
    created_at: str
    updated_at: str
    is_main_crop: Optional[bool] = None

    harvested_at: Optional[str] = None

    # ⭐⭐ 이 필드를 추가합니다. ⭐⭐
    suitable_regions: Optional[List[str]] = Field(None, description="재배에 적합한 지역 목록") # knowledge_base에서 오는 리스트 형태

    class Config:
        from_attributes = True

# ⭐ 새로 추가: HarvestCropRequest DTO ⭐
class HarvestCropRequest(BaseModel):
    user_id: int
    user_crop_id: int
    yield_info: Optional[str] = None # 수확량 또는 결과 정보

class DeleteAllUserCropsRequest(BaseModel):
    user_id: int

# ⭐⭐ 새로 추가: 체크리스트 항목 상태 업데이트 요청 DTO ⭐⭐
class ChecklistItemUpdateRequest(BaseModel):
    user_id: int
    user_crop_id: int
    item_id: str # 체크리스트 항목 고유 ID (예: "water-123", "sunlight-abc", "guide-456-0")
    is_completed: bool # 완료 여부

# ⭐⭐ 새로 추가: 체크리스트 항목 상태 응답 DTO (조회 시 사용) ⭐⭐
class ChecklistItemResponse(BaseModel):
    id: int
    user_id: int
    user_crop_id: int
    item_id: str
    is_completed: bool
    completed_at: Optional[str] = None # ISO 형식 문자열
    created_at: str
    updated_at: str
# ⭐⭐ 새로 추가: 작물 진행률 업데이트 요청 DTO ⭐⭐
class UserCropProgressUpdate(BaseModel):
    progress_percent: float = Field(..., ge=0.0, le=100.0) # 0.0 ~ 100.0 사이의 float 값

    class Config:
        from_attributes = True