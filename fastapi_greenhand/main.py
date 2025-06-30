# main.py
import os
import logging
from fastapi import FastAPI, HTTPException # HTTPException 임포트
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.responses import FileResponse # FileResponse 임포트

# 분리된 파일들에서 필요한 모듈/변수 임포트
from config import (
    UPLOAD_IMAGE_DIR, REPORT_DIR, CORS_ORIGINS,
    setup_gemini_api,
    genai_configured, global_gemini_model, global_gemini_flash_model
)
from database import Base, engine, SessionLocal, get_or_create_user
from routers import chatbot_router, diagnosis_router, crop_router

# --- 1. 환경 변수 로드 및 Gemini API 설정 ---
# config.py에서 setup_gemini_api가 호출되도록 이미 설정됨.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
print("FastAPI: Application startup sequence initiated.") # 시작 알림 추가

# --- 2. FastAPI 애플리케이션 초기화 ---
app = FastAPI(
    title="초록손 통합 AI 서비스",
    description="Gemini API를 활용한 챗봇, 식물 진단, 작물 추천 및 가이드 통합 서비스",
    version="1.0.0"
)

# --- 3. CORS 설정 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS, # config.py에서 가져온 CORS_ORIGINS 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. 이미지 및 보고서 저장 폴더 설정 및 정적 파일 서빙 ---
# FastAPI가 직접 서빙하는 정적 파일은 uploaded_images와 reports 뿐입니다.
# HTML, CSS, JS 등 프론트엔드 리소스는 Spring Boot가 서빙한다고 가정합니다.
os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

app.mount("/uploaded_images", StaticFiles(directory=UPLOAD_IMAGE_DIR), name="uploaded_images")
app.mount("/reports_static", StaticFiles(directory=REPORT_DIR), name="reports_static")

# HTML 파일을 FastAPI가 직접 서빙하는 StaticFiles 마운트 로직을 제거합니다.
# Spring Boot가 HTML 파일을 담당하므로 FastAPI는 이 기능을 가질 필요가 없습니다.

# --- 5. 라우터 등록 ---
app.include_router(chatbot_router.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(diagnosis_router.router, prefix="/diagnose", tags=["Plant Diagnosis"])
app.include_router(crop_router.router, prefix="/api", tags=["Crop Recommendation & Guide"])

# 파일 다운로드 라우터
@app.get("/files/{path_in_uploads_or_reports:path}")
async def download_file(path_in_uploads_or_reports: str):
    full_path = None
    if path_in_uploads_or_reports.startswith("uploaded_images/"):
        filename = path_in_uploads_or_reports.replace("uploaded_images/", "")
        full_path = os.path.join(UPLOAD_IMAGE_DIR, filename)
    elif path_in_uploads_or_reports.startswith("reports_static/"):
        filename = path_in_uploads_or_reports.replace("reports_static/", "")
        full_path = os.path.join(REPORT_DIR, filename)
    else:
        raise HTTPException(status_code=403, detail="Forbidden file path. Only 'uploaded_images' or 'reports_static' paths are allowed for direct file download.")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "application/octet-stream"
    if full_path.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif full_path.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif full_path.endswith(".jpg") or full_path.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif full_path.endswith(".png"):
        media_type = "image/png"
    elif full_path.endswith(".gif"):
        media_type = "image/gif"

    return FileResponse(path=full_path, media_type=media_type, filename=os.path.basename(full_path))


# --- 애플리케이션 실행 진입점 ---
if __name__ == "__main__":
    os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    Base.metadata.create_all(bind=engine) 
    logging.info("Database tables created/checked.")

    db = SessionLocal()
    try:
        get_or_create_user(db, user_id=1, username="default_test_user") 
    finally:
        db.close()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)