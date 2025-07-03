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

class AddUserCropRequest(BaseModel):
    user_id: int
    crop_id: str # knowledge_base에 정의된 작물의 고유 ID
    alias: Optional[str] = None

class DeleteUserCropRequest(BaseModel):
    user_id: int
    user_crop_id: int

# 추천 작물 반환용 모델 (Gemini AI 응답 구조와 일치)
class RecommendedCropResponse(BaseModel):
    # Gemini AI가 기본적으로 반환하는 필드 (필수)
    name: str = Field(..., description="작물 한글 이름 (예: '상추')")
    pot_size: str = Field(..., description="권장 화분 크기")
    water_amount: str = Field(..., description="권장 물의 양")
    soil_type: str = Field(..., description="권장 토양 유형")
    difficulty: str = Field(..., description="재배 난이도 (예: '하', '중', '상')")

    # knowledge_base에서 추가될 수 있는 필드들을 Optional로 설정
    # (FastAPI의 유효성 검사를 통과하기 위해)
    id: Optional[str] = Field(None, description="작물 고유 ID (knowledge_base의 ID)")
    cultivation_duration: Optional[str] = Field(None, description="권장 재배 기간")
    cultivation_location: Optional[List[str]] = Field(None, description="권장 재배 장소")
    suitable_regions: Optional[List[str]] = Field(None, description="적합 지역")
    thumbnail_image: Optional[str] = Field(None, description="작물 썸네일 이미지 URL")
    initial_preparations: Optional[List[str]] = Field(None, description="초기 준비물 및 과정")
    pest_control: Optional[str] = Field(None, description="흔한 병충해 및 간단 관리법")
    detailed_guide: Optional[Union[Dict[str, str], List[str]]] = Field(None, description="상세 재배 가이드")

    class Config:
        from_attributes = True # dict에서 Pydantic 모델로 매핑 허용

# 사용자 재배 작물 (DB에서 가져옴) 모델 <-- 이 부분이 누락되었습니다.
class UserCropResponse(BaseModel):
    id: int # 데이터베이스 PK
    user_id: str
    crop_id_from_kb: str # knowledge_base의 ID
    crop_name: str
    nick_name: Optional[str] = None
    
    environment: Optional[str] = None
    difficulty: Optional[str] = None
    pot_size: Optional[str] = None
    water_amount: Optional[str] = None
    soil_type: Optional[str] = None
    pest_control_info: Optional[str] = None # DB 모델의 pest_control_info와 일치
    thumbnail_image: Optional[str] = None

    growth_stage: Optional[str] = None
    care_instruction: Optional[Any] = None # JSON 문자열 또는 dict로 올 수 있으므로 Any
    other_notes: Optional[str] = None
    crop_status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class DeleteAllUserCropsRequest(BaseModel):
    user_id: int