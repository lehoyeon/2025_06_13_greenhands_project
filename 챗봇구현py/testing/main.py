# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse 
import os
import logging

# 로깅 설정 (애플리케이션 전체의 로깅을 여기서 설정)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 내부 모듈 임포트
from config import CORS_ORIGINS, UPLOAD_IMAGE_DIR, REPORT_DIR
from database import Base, engine, SessionLocal, get_or_create_user 
from services.gemini_service import configure_gemini # Gemini 설정 함수 임포트
from routers import chatbot_router, crop_router # 라우터 임포트

# FastAPI 애플리케이션 초기화
app = FastAPI(
    title="초록손 통합 AI 서비스",
    description="Gemini API를 활용한 챗봇, 식물 진단, 작물 추천 및 가이드 통합 서비스",
    version="1.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정 (현재 폴더 구조에 맞게)
# HTML, CSS, 이미지 파일들이 모두 프로젝트 루트에 있다고 가정합니다.
# 따라서 루트 디렉토리 자체를 정적 파일로 마운트합니다.
# 이 경우, 'index.html' 등이 자동으로 서빙될 수 있으며,
# 직접 파일명(예: http://localhost:8000/crop.css)으로 접근 가능합니다.
# 주의: 이 방식은 보안상 모든 파일이 노출될 수 있으므로, 실제 운영 환경에서는
# 정적 파일을 전용 'static' 폴더에 모아두고 그 폴더만 마운트하는 것이 좋습니다.
app.mount("/", StaticFiles(directory="."), name="root_static") 

# 추가적으로 'uploaded_images'와 'reports' 폴더도 명시적으로 마운트하여
# `/uploaded_images/` 및 `/reports_static/` 경로로 접근 가능하게 합니다.
app.mount("/uploaded_images", StaticFiles(directory=UPLOAD_IMAGE_DIR), name="uploaded_images")
app.mount("/reports_static", StaticFiles(directory=REPORT_DIR), name="reports_static")


# 애플리케이션 시작 시 DB 테이블 생성 및 Gemini 설정
@app.on_event("startup")
async def startup_event():
    # 필요한 디렉토리 생성
    os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    logger.info(f"Directories created/checked: {UPLOAD_IMAGE_DIR}, {REPORT_DIR}")

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/checked.")
    
    # 기본 사용자 생성 (필요하다면)
    db = SessionLocal()
    try:
        get_or_create_user(db, user_id=1, username="default_test_user")
    except Exception as e:
        logger.error(f"Failed to create default user on startup: {e}")
    finally:
        db.close()

    # Gemini API 설정
    if not configure_gemini():
        logger.critical("Gemini API 설정에 실패했습니다. 애플리케이션이 정상적으로 작동하지 않을 수 있습니다.")


# 라우터 포함 (라우터 객체들을 FastAPI 앱에 연결)
app.include_router(chatbot_router.router)
app.include_router(crop_router.router)


@app.get("/files/{path_in_uploads_or_reports:path}")
async def download_file(path_in_uploads_or_reports: str):
    """
    특정 경로의 파일을 다운로드합니다.
    이 엔드포인트는 주로 /uploaded_images/ 또는 /reports_static/ 경로로 직접 서빙되는 파일을
    추가적인 제어(예: 인증)와 함께 제공하고 싶을 때 사용될 수 있습니다.
    현재는 이미 StaticFiles로 해당 경로들이 마운트되어 있으므로, 
    특별한 로직이 없다면 이 라우터는 필수가 아닐 수 있습니다.
    """
    full_path = None
    if path_in_uploads_or_reports.startswith("uploaded_images/"):
        filename = path_in_uploads_or_reports.replace("uploaded_images/", "")
        full_path = os.path.join(UPLOAD_IMAGE_DIR, filename)
    elif path_in_uploads_or_reports.startswith("reports_static/"):
        filename = path_in_uploads_or_reports.replace("reports_static/", "")
        full_path = os.path.join(REPORT_DIR, filename)
    else:
        # FastAPI의 StaticFiles로 서빙되는 경로가 아닌 경우 403 Forbidden
        raise HTTPException(status_code=403, detail="Forbidden file path. Only 'uploaded_images' or 'reports_static' paths are allowed for direct /files/ access.")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found at: " + full_path)
    
    # MIME 타입 처리
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
    else:
        media_type = "application/octet-stream"

    return FileResponse(path=full_path, media_type=media_type, filename=os.path.basename(full_path))


if __name__ == "__main__":
    import uvicorn
    # uvicorn 실행: "모듈명:앱인스턴스명"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)