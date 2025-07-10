# config.py
import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging

# --- 환경 변수 로드 ---
# test.env와 img.env를 통합하거나, img.env가 test.env를 오버라이드하도록 설정
load_dotenv(dotenv_path='too.env') # .env 파일 하나로 통합 권장

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

UPLOAD_IMAGE_DIR = "uploaded_images"
REPORT_DIR = "reports"

# CORS 설정
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "*" # 개발 환경에서는 모든 출처 허용. 실제 배포 시에는 특정 출처만 허용하도록 변경 권장.
]

# 데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:user1234@192.168.0.30:3306/greenhand")

# Gemini API 설정 (초기화 및 모델 로드)
genai_configured = False
global_gemini_model = None  # 전역 Gemini 모델 인스턴스 (gemini-1.5-flash)
global_gemini_flash_model = None # gemini-1.5-flash 또는 'gemini-1.5-pro' 등

def setup_gemini_api():
    global genai_configured, global_gemini_model, global_gemini_flash_model
    if not GEMINI_API_KEY:
        logging.critical("FATAL ERROR: GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        raise RuntimeError("GOOGLE_API_KEY 환경 변수를 설정해야 합니다.")
    else:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            global_gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            global_gemini_flash_model = genai.GenerativeModel('gemini-1.5-flash') # 필요에 따라 다른 모델 설정
            logging.info("Gemini API가 성공적으로 설정되고 모델들이 로드되었습니다.")
            genai_configured = True
        except Exception as e:
            logging.critical(f"FATAL ERROR: Gemini API 구성 중 오류 발생: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Gemini API 구성 실패: {e}")

# 애플리케이션 시작 시 Gemini API 설정 함수 호출
setup_gemini_api()