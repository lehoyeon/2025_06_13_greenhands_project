# config.py
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(dotenv_path='test.env')
load_dotenv(dotenv_path='img.env', override=True) # 중복되는 키는 img.env가 우선

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# 이미지 및 보고서 저장 폴더 설정 (기존 폴더 구조 그대로 유지)
UPLOAD_IMAGE_DIR = "uploaded_images" 
REPORT_DIR = "reports"

# 데이터베이스 URL
DATABASE_URL = "mysql+pymysql://root:user1234@192.168.0.30:3306/greenhand"

# CORS 허용 출처
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "*" 
]