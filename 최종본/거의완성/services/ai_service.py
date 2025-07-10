# services/ai_service.py
import os
import base64
import uuid
import logging
import asyncio
import re
import json
from typing import Optional, List, Dict, Any, Union
import time

from fastapi import UploadFile, HTTPException
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ResourceExhausted, Aborted, NotFound, InternalServerError, ServiceUnavailable, GatewayTimeout, DeadlineExceeded

# ⭐ 변경: agricultural_knowledge_base 임포트 추가
from knowledge_base import get_crop_by_id, agricultural_knowledge_base

from config import UPLOAD_IMAGE_DIR, global_gemini_model, global_gemini_flash_model, genai_configured

async def save_base64_image(base64_string: str, mime_type: str) -> Optional[str]:
    """base64로 인코딩된 이미지를 UPLOAD_IMAGE_DIR에 저장합니다."""
    try:
        ext = mime_type.split('/')[-1]
        if 'jpeg' in ext: ext = 'jpg'
        elif 'png' in ext: ext = 'png'
        else: ext = 'bin' # 알 수 없는 MIME 타입에 대한 폴백

        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_IMAGE_DIR, filename)

        image_bytes = base64.b64decode(base64_string)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return f"/uploaded_images/{filename}" # FastAPI의 정적 마운트에 대한 URL 반환
    except Exception as e:
        logging.error(f"오류: base64에서 이미지 저장 실패: {type(e).__name__}: {e}")
        return None

async def save_uploaded_image_file(image_file: UploadFile) -> Optional[str]:
    """UploadFile 객체를 UPLOAD_IMAGE_DIR에 저장합니다."""
    try:
        ext = image_file.filename.split('.')[-1] if '.' in image_file.filename else 'bin'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_IMAGE_DIR, filename)

        with open(filepath, "wb") as f:
            while contents := await image_file.read(1024 * 1024): # 청크 단위로 읽기
                f.write(contents)

        return f"/uploaded_images/{filename}" # FastAPI의 정적 마운트에 대한 URL 반환
    except Exception as e:
        logging.error(f"오류: 업로드된 이미지 파일 저장 실패: {type(e).__name__}: {e}")
        return None

# ⭐ 변경: 반환 타입이 Dict[str, Any]로 변경됨
async def get_gemini_response_for_chat(user_query: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """Gemini 모델로부터 일반 채팅 응답을 받습니다. 페이지 이동 링크도 반환할 수 있습니다."""
    # ⭐ 중요: 일반 채팅 응답에 사용할 모델을 여기서 선택합니다.
    # 더 빠른 응답을 원하면 global_gemini_flash_model을 사용하세요.
    # 예: model_to_use = global_gemini_flash_model
    # 더 정확하지만 느린 응답을 원하면 global_gemini_model (보통 Pro 모델)을 사용하세요.
    model_to_use = global_gemini_model # 기본은 global_gemini_model (Pro)

    if not genai_configured or model_to_use is None:
        logging.error("Gemini API가 구성되지 않았거나 모델이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    # 사용자 쿼리를 소문자로 변환하여 대소문자 구분 없이 검색
    lower_user_query = user_query.lower()

    # ⭐⭐⭐ 1. 페이지 이동 키워드 감지 및 즉시 응답 로직 추가 (강화된 버전) ⭐⭐⭐
    # 각 HTML 페이지와 연결될 다양한 키워드 리스트를 정의합니다.
    # 사용자가 입력할 수 있는 다양한 표현을 추가할수록 매칭률이 높아집니다.
    page_mapping_keywords = {
        "img.html": ["질병 진단", "작물 진단", "병 진단", "사진 진단", "진단해줘", "아픈 식물", "문제있는 잎", "잎 진단", "사진으로 진단", "진찰", "어떻게 고쳐", "진단"],
        "crop.html": ["농작물 시뮬레이션", "작물 시뮬레이션", "재배 시뮬레이션", "키울 작물 추천", "어떤 작물", "작물 등록", "키워줘", "재배 시작", "작물 키운다", "작물등록", "재배등록", "시뮬레이션"],
        "main.html": ["내 농장", "메인 페이지", "홈 화면", "나의 농장", "내 작물", "내 작물 확인", "내 농장 확인", "농장"],
        "harvested_crops.html": ["수확한 작물", "그동안 키웠던", "수확 이력", "지난 작물", "수확 기록", "농장 기록", "수확"]
    }

    # 사용자 쿼리에 매핑되는 키워드가 있는지 확인
    for page_url, keywords in page_mapping_keywords.items():
        for keyword in keywords:
            if keyword.lower() in lower_user_query:
                # knowledge_base에서 해당 page_url에 해당하는 데이터를 찾아서 details를 가져옴
                # knowledge_base.py에서 link_page 필드를 기준으로 찾습니다.
                found_kb_data = None
                for kb_item_key, kb_item_data in agricultural_knowledge_base.items():
                    if "link_page" in kb_item_data and kb_item_data["link_page"] == page_url:
                        found_kb_data = kb_item_data
                        break

                if found_kb_data:
                    logging.info(f"사용자 쿼리 '{user_query}'에서 페이지 이동 키워드 '{keyword}' 감지. AI 호출 없이 바로 링크 반환. 대상 페이지: {page_url}")
                    # knowledge_base의 details 내용을 그대로 사용하며, JS에서 [XXX 바로가기]를 링크로 변환
                    response_text = found_kb_data["details"]
                    return {"response": response_text, "link_url": found_kb_data["link_page"]}
                else:
                    # knowledge_base에 직접 정의되지 않은 경우를 대비한 폴백 메시지
                    # 이 경우는 잘 발생하지 않아야 하지만, 만약을 위해 처리
                    logging.warning(f"페이지 이동 키워드 '{keyword}' 감지했으나, knowledge_base에 '{page_url}'에 대한 상세 정보 없음. 일반 응답으로 전환.")
                    response_text = f"요청하신 '{keyword}' 관련 페이지로 안내해 드릴게요. 잠시만 기다려주세요. ([{keyword} 바로가기])"
                    return {"response": response_text, "link_url": page_url}

    # ⭐⭐⭐ 2. 페이지 이동 키워드가 감지되지 않았을 경우 Gemini API 호출 ⭐⭐⭐
    parts_list = []
    if user_query:
        parts_list.append({"text": user_query})

    if image_path:
        local_file_path_for_gemini = os.path.join(UPLOAD_IMAGE_DIR, os.path.basename(image_path))
        if os.path.exists(local_file_path_for_gemini):
            try:
                with open(local_file_path_for_gemini, "rb") as f:
                    image_bytes_for_gemini = f.read()
                # MIME 타입 결정. image_path의 확장자가 신뢰할 수 있거나 올바르게 파생되었다고 가정합니다.
                mime_type_for_gemini = f"image/{local_file_path_for_gemini.split('.')[-1]}"
                if "jpg" in mime_type_for_gemini or "jpeg" in mime_type_for_gemini: mime_type_for_gemini = "image/jpeg"
                elif "png" in mime_type_for_gemini: mime_type_for_gemini = "image/png"

                parts_list.append({
                    "inline_data": {
                        "mime_type": mime_type_for_gemini,
                        "data": base64.b64encode(image_bytes_for_gemini).decode('utf-8')
                    }
                })
            except Exception as e:
                logging.error(f"Gemini용 저장된 이미지 읽기 실패 (챗봇): {type(e).__name__}: {e}")
        else:
            logging.warning(f"Gemini용 저장된 이미지 파일을 찾을 수 없습니다 (챗봇): {local_file_path_for_gemini}")

    if not parts_list:
        raise HTTPException(status_code=400, detail="텍스트 메시지나 이미지가 필요합니다.")

    contents = [{"role": "user", "parts": parts_list}]
    logging.info(f"Gemini 챗봇 호출. 이미지 존재 여부={bool(image_path)}, 쿼리='{user_query[:50]}...'")

    try:
        llm_response = await asyncio.to_thread(model_to_use.generate_content, contents) # ⭐ 선택된 모델 사용 ⭐
        generated_text = llm_response.text
        bot_response_content = generated_text.strip()
    except InvalidArgument as e:
        logging.error(f"Gemini 유효하지 않은 인수: {e}. 내용: {contents}")
        raise HTTPException(status_code=400, detail=f"AI 모델에 전달된 인자가 유효하지 않습니다. 상세: {str(e)}")
    except ResourceExhausted as e:
        logging.error(f"Gemini 리소스 소진: {e}")
        raise HTTPException(status_code=429, detail=f"AI 모델 호출 할당량이 소진되었습니다. 잠시 후 다시 시도해주세요. 상세: {str(e)}")
    except GoogleAPIError as e:
        logging.error(f"Google API 오류: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Google AI API 통신 중 오류 발생: {str(e)}")
    except Exception as e:
        logging.error(f"예상치 못한 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        bot_response_content = f"죄송합니다. AI 응답 생성 중 오류가 발생했습니다: {str(e)}"

    # ⭐ 변경: 일반적인 텍스트 응답의 경우에도 link_url을 None으로 포함하여 반환
    return {"response": bot_response_content, "link_url": None}

async def get_gemini_plant_diagnosis(image_base64: str, mime_type: str, prompt: str) -> dict:
    """Gemini 모델로부터 JSON 형식의 식물 진단 응답을 받습니다."""
    if not genai_configured or global_gemini_model is None:
        logging.error("Gemini API가 구성되지 않았거나 모델이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    # image_base64가 이미 Base64 인코딩된 문자열이므로,
    # MIME 타입 유효성 검사만 합니다.
    if not image_base64 or not mime_type.startswith("image/"):
        logging.error(f"식물 진단을 위해 유효하지 않은 이미지 데이터 수신. base64 존재 여부: {bool(image_base64)}, mime_type: {mime_type}")
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 필요합니다.")

    try:
        # JSON 출력을 명시적으로 요청하는 프롬프트 (기존과 동일)
        full_prompt_with_json_instruction = (
            "당신은 식물 진단 전문가 챗봇 '초록손'입니다. "
            "주어진 이미지와 사용자 질문을 바탕으로 식물의 건강 상태, 질병 여부, "
            "예상되는 질병명, 심각도, 그리고 간략한 관리 방법을 제공합니다. "
            "응답은 반드시 다음 JSON 형식으로만 제공해야 합니다. "
            "```json\n"
            "{\n"
            " \"diagnosis_result\": \"(간결한 진단 결과 요약, 20자 이내)\",\n"
            " \"diagnosis_details\": \"특징: (식물의 주요 증상, 발생 부위, 색 변화 등 육안으로 관찰되는 상세 특징을 2~3문장으로 설명).\\n\\n원인: (질병의 구체적인 원인균, 환경적 요인, 전염 경로 등을 2~3문장으로 상세하게 설명).\\n\\n해결 방안: (질병 확산 방지, 치료법, 재배 환경 개선, 예방 수칙 등 구체적이고 실용적인 방법을 3~5문장으로 충분히 상세하게 설명). 각 항목은 단 한 번만 나타나야 하며, 해당 항목의 내용만 간결하고 명확하게 작성합니다. 각 항목 사이에는 두 번의 줄바꿈(\\n\\n)을 사용하여 구분합니다. 다른 내용은 포함하지 마세요.\",\n"
            " \"severity\": \"(정상/경미/보통/심각 중 하나)\",\n"
            " \"plant_name\": \"(진단된 작물 이름, 모르면 '알 수 없음')\"\n"
            "}\n"
            "```"
            "다른 설명이나 추가적인 문장은 일절 포함하지 마세요. 오직 JSON만 출력합니다.\n\n"
            f"{prompt}"
        )

        contents = [{"role": "user", "parts": [
            {"text": full_prompt_with_json_instruction},
            {
                "inline_data": {
                    "mime_type": mime_type,
                    # ⭐⭐⭐ 이 부분을 이렇게 수정하세요 ⭐⭐⭐
                    # image_base64는 이미 Base64로 인코딩된 문자열입니다.
                    # Gemini API는 Base64 문자열을 'data' 필드에 직접 받습니다.
                    "data": image_base64
                }
            }
        ]}]

        # JSON 출력을 강력히 권장하기 위해 generation_config 사용
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2, # 구조화된 출력을 위해 온도 낮춤
            "max_output_tokens": 1024, # 최대 출력 토큰을 충분히 확보
            "top_p": 0.9,
            "top_k": 20
        }

        response = await asyncio.to_thread(
            global_gemini_model.generate_content, # 이미지 진단은 Pro 모델 (Vision) 사용
            contents,
            generation_config=generation_config
        )

        raw_gemini_response_text = response.text
        logging.info(f"Gemini 원시 응답 (식물 진단): {raw_gemini_response_text[:500]}...")

        parsed_data = {}
        try:
            # 코드 블록에서 JSON 추출 시도, 실패 시 직접 파싱
            json_match = re.search(r"```json\s*(\{.*\})\s*```", raw_gemini_response_text, re.DOTALL)
            if json_match:
                json_string = json_match.group(1)
            else:
                json_string = raw_gemini_response_text

            parsed_data = json.loads(json_string) # JSON 문자열을 파이썬 딕셔너리로 변환
        except json.JSONDecodeError as e:
            logging.error(f"JSON 파싱 실패 (식물 진단): {e}. 원시 응답: {raw_gemini_response_text}")
            # JSON 파싱 실패 시, 기본 텍스트 응답으로 폴백
            parsed_data = {
                "diagnosis_result": "AI 응답 파싱 오류",
                "diagnosis_details": f"AI가 JSON 형식으로 응답하지 않았습니다. 원본 응답:\n{raw_gemini_response_text}",
                "severity": "알 수 없음",
                "plant_name": "알 수 없음"
            }
        except Exception as e:
            logging.error(f"파싱 중 예상치 못한 오류 발생 (식물 진단): {type(e).__name__}: {e}")
            parsed_data = {
                "diagnosis_result": "AI 응답 처리 중 오류",
                "diagnosis_details": f"AI 응답 처리 중 오류가 발생했습니다. 원본 응답:\n{raw_gemini_response_text}",
                "severity": "알 수 없음",
                "plant_name": "알 수 없음"
            }

        return {
            "diagnosis_result": parsed_data.get("diagnosis_result", "진단 결과 없음"),
            "diagnosis_details": parsed_data.get("diagnosis_details", parsed_data.get("diagnosis_details", raw_gemini_response_text)),
            "severity": parsed_data.get("severity", "알 수 없음"),
            "plant_name": parsed_data.get("plant_name", "알 수 없음"),
            "image_url": parsed_data.get("image_url", None) # FastAPI는 이미지 URL을 반환하지 않고 Spring Boot가 처리합니다.
        }

    except InvalidArgument as e:
        logging.error(f"Gemini 유효하지 않은 인수 (식물 진단): {e}. 내용: {contents}")
        raise HTTPException(status_code=400, detail=f"AI 모델에 전달된 인자가 유효하지 않습니다. 상세: {str(e)}")
    except ResourceExhausted as e:
        logging.error(f"Gemini 리소스 소진 (식물 진단): {e}")
        raise HTTPException(status_code=429, detail=f"AI 모델 호출 할당량이 소진되었습니다. 잠시 후 다시 시도해주세요. 상세: {str(e)}")
    except GoogleAPIError as e:
        logging.error(f"Google API 오류 (식물 진단): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Google AI API 통신 중 오류 발생: {str(e)}")
    except Exception as e:
        logging.error(f"Gemini 호출 중 예상치 못한 오류 발생 (식물 진단): {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"식물 진단 중 오류 발생: {str(e)}. 상세 오류: {type(e).__name__}")


async def get_gemini_crop_recommendation(environment: str, duration: str, region: str) -> List[Dict[str, Any]]:
    """환경, 재배 기간, 지역에 따라 작물을 추천합니다. JSON 배열 형식으로 작물 정보를 반환합니다."""
    if not genai_configured or global_gemini_flash_model is None:
        logging.error("Gemini API가 구성되지 않았거나 global_gemini_flash_model이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    prompt_text = (
        f"재배 환경: {environment}, 재배 기간: {duration}, 지역: {region}에 적합한 작물을 추천하세요."
        " 각 작물에 대해 **id (knowledge_base에 있는 고유 ID),** 이름, 화분 크기, 물의 양, 토양 유형, 재배 난이도를 포함합니다."
        " 한국어로 답변해주세요."
        " (예시 ID: lettuce, radish, tomato, basil, potato와 같이 knowledge_base에 정의된 정확한 ID를 사용해야 합니다.)"
    )

    contents = [
        {"role": "user", "parts": [{"text": prompt_text}]}
    ]

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING", "description": "작물 고유 ID (knowledge_base의 ID)", "enum": ["lettuce", "radish", "tomato", "basil", "potato"]},
                    "name": {"type": "STRING", "description": "작물 이름"},
                    "pot_size": {"type": "STRING", "description": "권장 화분 크기"},
                    "water_amount": {"type": "STRING", "description": "권장 물의 양"},
                    "soil_type": {"type": "STRING", "description": "권장 토양 유형"},
                    "difficulty": {"type": "STRING", "description": "재배 난이도 (예: '하', '중', '상')"}
                },
                "required": ["id", "name", "pot_size", "water_amount", "soil_type", "difficulty"]
            }
        },
        "temperature": 0.3,
        "max_output_tokens": 512,
        "top_p": 0.8,
        "top_k": 40
    }

    try:
        logging.info(f"Gemini 추천 API 호출 시도: 쿼리='{environment}, {duration}, {region}'")
        start_time = time.time()

        response = await asyncio.to_thread(
            global_gemini_flash_model.generate_content,
            contents,
            generation_config=generation_config
        )
        end_time = time.time()
        logging.info(f"Gemini 추천 API 응답 수신 (소요 시간: {end_time - start_time:.2f}초)")

        output_json_string = response.text
        logging.info(f"Gemini 추천 API 원시 응답: {output_json_string[:500]}...")

        crops = json.loads(output_json_string)

        if not isinstance(crops, list):
            logging.error(f"API 응답이 예상된 JSON 배열 형식이 아님: {output_json_string}")
            raise TypeError("API 응답이 예상된 JSON 배열 형식이 아닙니다.")

        # ⭐⭐⭐ 이 부분을 추가하여 knowledge_base에서 썸네일 이미지를 가져와 합칩니다 ⭐⭐⭐
        processed_crops = []
        for crop_item in crops:
            crop_id = crop_item.get('id')
            if crop_id:
                kb_data = get_crop_by_id(crop_id) # knowledge_base에서 해당 ID의 상세 정보 가져옴
                if kb_data:
                    # AI 응답 데이터에 knowledge_base의 썸네일_이미지 경로를 추가
                    if kb_data.get('thumbnail_image'):
                        crop_item['thumbnail_image'] = kb_data['thumbnail_image']
                    # 필요한 경우 expected_cultivation_days 등 다른 KB 정보도 여기서 합칠 수 있습니다.
                    # (현재 crop_router.py에서 또 합치고 있으므로 중복될 수 있습니다. 하지만 썸네일은 여기서 합쳐야 AI 응답에 포함됩니다.)
                    if 'watering_frequency_detail' in kb_data: # 물 주기 상세 정보
                        crop_item['watering_frequency_detail'] = kb_data['watering_frequency_detail']
                    if 'expected_cultivation_days' in kb_data: # 예상 재배 일수
                        crop_item['expected_cultivation_days'] = kb_data['expected_cultivation_days']
                    if 'cultivation_location' in kb_data: # 재배 장소 (실내/실외)
                        crop_item['cultivation_location'] = kb_data['cultivation_location']
                    if 'suitable_regions' in kb_data: # 적합 지역
                        crop_item['suitable_regions'] = kb_data['suitable_regions']
                    if 'initial_preparations' in kb_data: # 초기 준비물
                        crop_item['initial_preparations'] = kb_data['initial_preparations']
                    if 'pest_control' in kb_data: # 병충해
                        crop_item['pest_control'] = kb_data['pest_control']
                    if 'cultivation_duration' in kb_data: # 재배 기간
                        crop_item['cultivation_duration'] = kb_data['cultivation_duration']

                else:
                    logging.warning(f"Knowledge base에서 작물 ID '{crop_id}'를 찾을 수 없습니다. 썸네일 이미지 없음.")
            processed_crops.append(crop_item) # 처리된 작물 아이템 추가

        logging.info(f"Gemini API 응답 (작물 추천 - KB 정보 합쳐짐): {json.dumps(processed_crops, ensure_ascii=False, indent=2)}")
        return processed_crops # ⭐ 처리된 리스트 반환 ⭐

    except ResourceExhausted as e:
        logging.error(f"Gemini API 할당량 초과 (429): {e}")
        raise HTTPException(status_code=429, detail=f"AI 모델 호출 할당량이 소진되었습니다. 잠시 후 다시 시도해주세요. 상세: {str(e)}")
    except InvalidArgument as e:
        logging.error(f"Gemini API 유효하지 않은 인수 (400): {e}. 내용: {contents}")
        raise HTTPException(status_code=400, detail=f"AI 모델에 전달된 인자가 유효하지 않습니다. 상세: {str(e)}")
    except DeadlineExceeded as e:
        logging.error(f"Gemini API 응답 시간 초과 (504): {e}")
        raise HTTPException(status_code=504, detail=f"AI 응답 시간이 너무 오래 걸립니다. 다시 시도해주세요. 상세: {str(e)}")
    except GoogleAPIError as e:
        logging.error(f"Google API 오류 (5xx): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Google AI API 통신 중 오류 발생: {str(e)}")
    except json.JSONDecodeError as e:
        logging.error(f"API 응답 JSON 디코딩 실패 (작물 추천): {e}. 원시 응답: {output_json_string}")
        raise HTTPException(status_code=500, detail=f"AI 모델 응답 JSON 형식 오류: {e}. 원시 응답: {output_json_string}")
    except TypeError as e:
        logging.error(f"API 응답 형식 오류 (작물 추천 - List 아님): {e}")
        raise HTTPException(status_code=500, detail=f"AI 모델 응답 형식 오류: {e}")
    except Exception as e:
        logging.error(f"알 수 없는 오류 발생 (작물 추천): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"작물 추천 중 알 수 없는 오류: {str(e)}")


async def get_gemini_crop_guide(crop_name: str) -> list:
    """특정 작물에 대한 재배 가이드를 생성합니다. 단계별 가이드를 JSON 배열 형식으로 반환합니다."""
    if not genai_configured or global_gemini_flash_model is None:
        logging.error("Gemini API가 구성되지 않았거나 global_gemini_flash_model이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

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
        response = await asyncio.to_thread(
            global_gemini_flash_model.generate_content,
            contents,
            generation_config=generation_config
        )

        output_json_string = response.text
        guide_steps = json.loads(output_json_string)

        if not isinstance(guide_steps, list):
            raise TypeError("가이드 단계가 배열 형식이 아닙니다.")

        logging.info(f"Gemini API 응답 (작물 가이드): {json.dumps(guide_steps, ensure_ascii=False, indent=2)}")
        return guide_steps

    except (InvalidArgument, GoogleAPIError, ResourceExhausted) as e:
        logging.error(f"Gemini API 호출 실패 (작물 가이드): {e}")
        raise HTTPException(status_code=500, detail=f"API 호출 실패: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"API 응답 JSON 디코딩 실패 (작물 가이드): {e}")
        raise HTTPException(status_code=500, detail=f"API 응답 JSON 디코딩 실패: {e}. 원시 응답: {output_json_string}")
    except TypeError as e:
        logging.error(f"가이드 단계 형식 오류 (작물 가이드): {e}")
        raise HTTPException(status_code=500, detail=f"가이드 단계 형식 오류: {e}")
    except Exception as e:
        logging.error(f"알 수 없는 오류 발생 (작물 가이드): {e}")
        raise HTTPException(status_code=500, detail=f"알 수 없는 오류: {e}")