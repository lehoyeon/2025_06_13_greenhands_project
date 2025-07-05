# services/ai_service.py
import os
import base64
import uuid
import logging
import asyncio
import re
import json
from typing import Optional # Optional 타입 힌트를 위해 필요

from fastapi import UploadFile, HTTPException
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ResourceExhausted, Aborted, NotFound, InternalServerError, ServiceUnavailable, GatewayTimeout, DeadlineExceeded # 모든 예외 임포트 유지

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

async def get_gemini_response_for_chat(user_query: str, image_path: Optional[str] = None) -> str:
    """Gemini 모델로부터 일반 채팅 응답을 받습니다."""
    if not genai_configured or global_gemini_model is None:
        logging.error("Gemini API가 구성되지 않았거나 모델이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

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
        llm_response = await asyncio.to_thread(global_gemini_model.generate_content, contents)
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
    
    # 중요: 여기서 HTML 링크 변환 로직은 제거됩니다.
    # 챗봇은 순수한 마크다운 링크를 반환하며, Spring Boot (또는 JS)가 이를 파싱해야 합니다.
    return bot_response_content

async def get_gemini_plant_diagnosis(image_base64: str, mime_type: str, prompt: str) -> dict:
    """Gemini 모델로부터 JSON 형식의 식물 진단 응답을 받습니다."""
    if not genai_configured or global_gemini_model is None:
        logging.error("Gemini API가 구성되지 않았거나 모델이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    if not image_base64 or not mime_type.startswith("image/"):
        logging.error(f"식물 진단을 위해 유효하지 않은 이미지 데이터 수신. base64 존재 여부: {bool(image_base64)}, mime_type: {mime_type}")
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 필요합니다.")
        
    try:
        # JSON 출력을 명시적으로 요청하는 프롬프트
        # diagnosis_details 내용 내부에 "특징:", "원인:", "해결 방안:"을 명시적으로 포함하도록 수정
        full_prompt_with_json_instruction = (
            "당신은 식물 진단 전문가 챗봇 '초록손'입니다. "
            "주어진 이미지와 사용자 질문을 바탕으로 식물의 건강 상태, 질병 여부, "
            "예상되는 질병명, 심각도, 그리고 간략한 관리 방법을 제공합니다. "
            "응답은 반드시 다음 JSON 형식으로만 제공해야 합니다. "
            "```json\n"
            "{\n"
            "   \"diagnosis_result\": \"(간결한 진단 결과 요약, 20자 이내)\",\n"
            "   \"diagnosis_details\": \"특징: (식물의 주요 증상, 발생 부위, 색 변화 등 육안으로 관찰되는 상세 특징을 2~3문장으로 설명).\\n\\n원인: (질병의 구체적인 원인균, 환경적 요인, 전염 경로 등을 2~3문장으로 상세하게 설명).\\n\\n해결 방안: (질병 확산 방지, 치료법, 재배 환경 개선, 예방 수칙 등 구체적이고 실용적인 방법을 3~5문장으로 충분히 상세하게 설명). 각 항목은 단 한 번만 나타나야 하며, 해당 항목의 내용만 간결하고 명확하게 작성합니다. 각 항목 사이에는 두 번의 줄바꿈(\\n\\n)을 사용하여 구분합니다. 다른 내용은 포함하지 마세요.\",\n" # <--- 이 부분이 수정되었습니다.
            "   \"severity\": \"(정상/경미/보통/심각 중 하나)\",\n"
            "   \"plant_name\": \"(진단된 작물 이름, 모르면 '알 수 없음')\"\n"
            "}\n"
            "```"
            "다른 설명이나 추가적인 문장은 일절 포함하지 마세요. 오직 JSON만 출력합니다.\n\n"
            f"{prompt}" # 사용자 프롬프트를 마지막에 추가하여 AI가 이를 기반으로 응답하도록 함
        )
        
        contents = [{"role": "user", "parts": [
            {"text": full_prompt_with_json_instruction},
            {
                "inline_data": {
                    "mime_type": mime_type,
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
            global_gemini_model.generate_content,
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


async def get_gemini_crop_recommendation(environment: str, duration: str, region: str) -> list: # <-- 이렇게 변경합니다.
    """환경, 재배 기간, 지역에 따라 작물을 추천합니다. JSON 배열 형식으로 작물 정보를 반환합니다."""
    if not genai_configured or global_gemini_flash_model is None:
        logging.error("Gemini API가 구성되지 않았거나 global_gemini_flash_model이 로드되지 않았습니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    # 프롬프트도 변경된 인수에 맞춰 조정
    prompt_text = (
        f"재배 환경: {environment}, 재배 기간: {duration}, 지역: {region}에 적합한 작물을 추천하세요."
        " 각 작물에 대해 **id (knowledge_base에 있는 고유 ID),** 이름, 화분 크기, 물의 양, 토양 유형, 재배 난이도를 포함합니다." # id 요청 추가
        " 한국어로 답변해주세요."
        " (예시 ID: lettuce, radish, tomato, basil, potato와 같이 knowledge_base에 정의된 정확한 ID를 사용해야 합니다.)" # ID 예시 제공
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
                    "id": {"type": "STRING", "description": "작물 고유 ID (knowledge_base의 ID)", "enum": ["lettuce", "radish", "tomato", "basil", "potato"]}, # 여기에 id 추가 및 enum으로 가능한 ID 명시
                    "name": {"type": "STRING", "description": "작물 이름"},
                    "pot_size": {"type": "STRING", "description": "권장 화분 크기"},
                    "water_amount": {"type": "STRING", "description": "권장 물의 양"},
                    "soil_type": {"type": "STRING", "description": "권장 토양 유형"},
                    "difficulty": {"type": "STRING", "description": "재배 난이도 (예: '하', '중', '상')"}
                },
                # 'id'를 필수 필드에 추가
                "required": ["id", "name", "pot_size", "water_amount", "soil_type", "difficulty"]
            }
        },
        "temperature": 0.3,
        "max_output_tokens": 512,
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
        crops = json.loads(output_json_string)

        if not isinstance(crops, list):
            raise TypeError("API 응답이 예상된 JSON 배열 형식이 아닙니다.")

        # 추가: knowledge_base에서 상세 정보 합치기 (필수 아님, 선택 사항)
        # Gemini가 제공하는 기본 정보 외에 knowledge_base의 상세 정보도 함께 보내고 싶다면
        # for crop_item in crops:
        #     kb_data = get_crop_by_id(crop_item.get('id'))
        #     if kb_data:
        #         crop_item.update(kb_data) # knowledge_base의 데이터를 현재 작물 데이터에 병합

        logging.info(f"Gemini API 응답 (작물 추천): {json.dumps(crops, ensure_ascii=False, indent=2)}")
        return crops

    except (InvalidArgument, GoogleAPIError, ResourceExhausted) as e:
        logging.error(f"Gemini API 호출 실패 (작물 추천): {e}")
        raise HTTPException(status_code=500, detail=f"API 호출 실패: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"API 응답 JSON 디코딩 실패 (작물 추천): {e}. 원시 응답: {output_json_string}")
        raise HTTPException(status_code=500, detail=f"API 응답 JSON 디코딩 실패: {e}. 원시 응답: {output_json_string}")
    except TypeError as e:
        logging.error(f"API 응답 형식 오류 (작물 추천): {e}")
        raise HTTPException(status_code=500, detail=f"API 응답 형식 오류: {e}")
    except Exception as e:
        logging.error(f"알 수 없는 오류 발생 (작물 추천): {e}")
        raise HTTPException(status_code=500, detail=f"알 수 없는 오류: {e}")


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
