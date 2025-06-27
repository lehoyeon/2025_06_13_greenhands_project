# routers/crop_router.py
from fastapi import APIRouter, HTTPException
import json
import logging
from typing import List

# 프로젝트 내부 모듈 임포트
from models.crop import CropRecommendationRequest, CropGuideRequest
from services.gemini_service import generate_content_with_gemini 

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/recommend-crop")
async def recommend_crop(data: CropRecommendationRequest):
    """
    수확 희망 시기와 재배 장소에 따라 작물을 추천합니다.
    응답은 JSON 배열 형식으로 작물 정보(이름, 화분 크기, 물의 양, 토양 유형, 난이도)를 반환합니다.
    """
    harvest = data.harvest
    environment = data.environment

    prompt_text = (
        f"수확 희망 시기: {harvest}, 재배 장소: {environment}에 적합한 작물을 추천하세요."
        " 각 작물에 대해 이름, 화분 크기, 물의 양, 토양 유형, 재배 난이도를 포함합니다."
    )

    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt_text}
            ]
        }
    ]
    
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING", "description": "작물 이름"},
                    "pot_size": {"type": "STRING", "description": "권장 화분 크기"},
                    "water_amount": {"type": "STRING", "description": "권장 물의 양"},
                    "soil_type": {"type": "STRING", "description": "권장 토양 유형"},
                    "difficulty": {"type": "STRING", "description": "재배 난이도 (예: '하', '중', '상')"}
                },
                "required": ["name", "pot_size", "water_amount", "soil_type", "difficulty"]
            }
        },
        "temperature": 0.3,
        "max_output_tokens": 512,
        "top_p": 0.8,
        "top_k": 40
    }

    try:
        output_json_string = await generate_content_with_gemini('gemini-2.0-flash', contents, generation_config)
        crops = json.loads(output_json_string)

        if not isinstance(crops, list):
            raise TypeError("API 응답이 예상된 JSON 배열 형식이 아닙니다.")

        logger.info(f"Gemini API 응답 (recommend-crop): {json.dumps(crops, ensure_ascii=False, indent=2)}")
        return crops

    except Exception as e: 
        logger.error(f"Error during Gemini call (recommend-crop): {e}")
        raise # generate_content_with_gemini에서 이미 HTTPException으로 변환하여 발생시키므로 다시 발생시킴


@router.post("/api/crop-guide")
async def crop_guide(data: CropGuideRequest):
    """
    특정 작물에 대한 재배 가이드를 생성합니다.
    응답은 JSON 배열 형식으로 단계별 가이드를 반환합니다.
    """
    crop_name = data.crop_name

    if not crop_name:
        raise HTTPException(status_code=400, detail="작물 이름이 필요합니다.")

    prompt_text = f"작물 '{crop_name}'의 재배 가이드를 단계별로 상세히 설명하세요. 각 단계는 짧고 명확하게 설명하고, 다음 JSON 배열 형식으로 출력하세요: [\"1. 첫 번째 단계 설명\", \"2. 두 번째 단계 설명\", ...]. 설명은 포함하지 마세요."

    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt_text}
            ]
        }
    ]

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "temperature": 0.5,
        "max_output_tokens": 1024,
        "top_p": 0.8,
        "top_k": 40
    }

    try:
        output_json_string = await generate_content_with_gemini('gemini-2.0-flash', contents, generation_config)
        guide_steps = json.loads(output_json_string)

        if not isinstance(guide_steps, list):
            raise TypeError("가이드 단계가 배열 형식이 아닙니다.")

        logger.info(f"Gemini API 응답 (crop-guide): {json.dumps(guide_steps, ensure_ascii=False, indent=2)}")
        return guide_steps

    except Exception as e:
        logger.error(f"Error during Gemini call (crop-guide): {e}")
        raise # generate_content_with_gemini에서 이미 HTTPException으로 변환하여 발생시키므로 다시 발생시킴