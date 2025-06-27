# services/gemini_service.py
import google.generativeai as genai
import asyncio
import base64
import logging
import uuid 
from fastapi import UploadFile, HTTPException 
from typing import Optional

from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ResourceExhausted

from config import GEMINI_API_KEY, UPLOAD_IMAGE_DIR 
import os

logger = logging.getLogger(__name__)

genai_configured = False
global_gemini_model = None 
global_gemini_flash_model = None 

def configure_gemini():
    """
    Gemini API를 설정하고 모델 인스턴스를 로드합니다.
    이 함수는 애플리케이션 시작 시 `main.py`에서 한 번 호출됩니다.
    """
    global genai_configured, global_gemini_model, global_gemini_flash_model
    if not GEMINI_API_KEY:
        logger.critical("FATAL ERROR: GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        raise RuntimeError("GOOGLE_API_KEY 환경 변수를 설정해야 합니다.")
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        global_gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        global_gemini_flash_model = genai.GenerativeModel('gemini-2.0-flash')
        genai_configured = True
        logger.info("Gemini API가 성공적으로 설정되고 모델들이 로드되었습니다.")
        return True
    except Exception as e:
        logger.critical(f"FATAL ERROR: Gemini API 구성 중 오류 발생: {type(e).__name__}: {e}")
        raise RuntimeError(f"Gemini API 구성 실패: {e}")

async def generate_content_with_gemini(model_name: str, contents: list, generation_config: dict = None):
    """
    지정된 Gemini 모델로 콘텐츠를 생성하고, API 관련 오류를 FastAPI HTTPException으로 변환합니다.
    """
    if not genai_configured:
        logger.error("Gemini API가 설정되지 않았습니다. configure_gemini()가 먼저 호출되어야 합니다.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. 서버 설정을 확인하세요.")

    model = None
    if model_name == 'gemini-1.5-flash':
        model = global_gemini_model
    elif model_name == 'gemini-2.0-flash':
        model = global_gemini_flash_model
    else:
        logger.error(f"Unsupported Gemini model name: {model_name}")
        raise HTTPException(status_code=400, detail=f"지원하지 않는 AI 모델 이름입니다: {model_name}")

    if model is None:
        logger.error(f"Requested Gemini model ({model_name}) is not loaded.")
        raise HTTPException(status_code=503, detail=f"요청된 AI 모델 ({model_name})이 로드되지 않았습니다. 서버 상태를 확인하세요.")

    try:
        response = await asyncio.to_thread(model.generate_content, contents, generation_config=generation_config)
        return response.text
    except InvalidArgument as e:
        logger.error(f"Gemini Invalid Argument error: {e}. Contents: {contents}")
        raise HTTPException(status_code=400, detail=f"AI 모델에 전달된 인자가 유효하지 않습니다. 상세: {str(e)}")
    except ResourceExhausted as e:
        logger.error(f"Gemini Resource Exhausted error: {e}")
        raise HTTPException(status_code=429, detail=f"AI 모델 호출 할당량이 소진되었습니다. 잠시 후 다시 시도해주세요. 상세: {str(e)}")
    except GoogleAPIError as e:
        logger.error(f"Google API Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Google AI API 통신 중 오류 발생: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during Gemini call ({model_name}): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"AI 응답 생성 중 예기치 않은 오류가 발생했습니다: {str(e)}")

async def save_uploaded_image_file(image_file: UploadFile) -> Optional[str]:
    """
    업로드된 이미지 파일을 로컬의 `UPLOAD_IMAGE_DIR`에 저장하고,
    웹에서 접근 가능한 URL 경로를 반환합니다.
    """
    try:
        ext = image_file.filename.split('.')[-1].lower() if '.' in image_file.filename else 'bin'
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']: 
            logger.warning(f"Unsupported file type uploaded: {ext}")
            raise HTTPException(status_code=400, detail="지원하지 않는 이미지 파일 형식입니다.")

        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_IMAGE_DIR, filename)

        with open(filepath, "wb") as f:
            while contents := await image_file.read(1024 * 1024): 
                f.write(contents)
        
        # FastAPI의 StaticFiles 경로에 맞춰 URL 반환
        # 기존 HTML 파일들이 루트에 있고, /uploaded_images 로 마운트하므로 이 경로를 그대로 사용
        return f"/uploaded_images/{filename}" 
    except HTTPException: 
        raise
    except Exception as e:
        logger.error(f"ERROR: Failed to save uploaded image file: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"이미지 파일 저장 중 오류 발생: {str(e)}")


async def get_image_parts_for_gemini(image_url: str, mime_type: Optional[str]) -> Optional[dict]:
    """
    로컬에 저장된 이미지의 URL을 받아 Gemini API에 전달할 수 있는
    `inline_data` (base64 인코딩된 이미지) 형식으로 변환합니다.
    """
    # image_url은 "/uploaded_images/{filename}" 형태
    # 실제 파일 시스템 경로로 변환
    relative_path = image_url.replace("/uploaded_images/", "")
    local_file_path = os.path.join(UPLOAD_IMAGE_DIR, relative_path)

    if not os.path.exists(local_file_path):
        logger.warning(f"Image file not found for Gemini processing: {local_file_path}")
        return None
    
    try:
        with open(local_file_path, "rb") as f:
            image_bytes = f.read()
        
        # MIME 타입 추정 또는 전달된 값 사용
        if not mime_type: 
            file_ext = os.path.splitext(local_file_path)[1].lower()
            if file_ext == '.jpg' or file_ext == '.jpeg': mime_type = 'image/jpeg'
            elif file_ext == '.png': mime_type = 'image/png'
            elif file_ext == '.gif': mime_type = 'image/gif'
            else: 
                mime_type = 'application/octet-stream' 
                logger.warning(f"Could not determine MIME type for {image_url}. Using default: {mime_type}")
        elif "jpg" in mime_type or "jpeg" in mime_type: 
            mime_type = "image/jpeg"
        elif "png" in mime_type:
            mime_type = "image/png"
        elif "gif" in mime_type:
            mime_type = "image/gif"
        
        return {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode('utf-8')
            }
        }
    except Exception as e:
        logger.error(f"Failed to process image {local_file_path} for Gemini: {type(e).__name__}: {e}")
        return None