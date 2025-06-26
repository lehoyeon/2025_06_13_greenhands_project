from fastapi import FastAPI, HTTPException, Request, Depends, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os
import google.generativeai as genai
import asyncio
import base64
import uuid
from fastapi.responses import FileResponse, HTMLResponse

# StaticFiles 임포트 (정적 파일 서빙용)
from fastapi.staticfiles import StaticFiles

# CORS 설정
from fastapi.middleware.cors import CORSMiddleware

# SQLAlchemy 관련 임포트
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func

# 보고서 생성에 필요한 라이브러리
import pandas as pd
from datetime import datetime
from docx import Document
import re

# Gemini API 관련 예외를 위한 추가 임포트 (가장 중요!)
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ResourceExhausted, Aborted, NotFound, InternalServerError, ServiceUnavailable, GatewayTimeout, DeadlineExceeded

# --- 1. 환경 변수 로드 및 Gemini API 설정 ---
load_dotenv(dotenv_path='test.env') # 챗봇 API 키 (GOOGLE_API_KEY)
load_dotenv(dotenv_path='img.env', override=True) # 이미지 진단 API 키 (GOOGLE_API_KEY가 중복될 수 있음)

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

genai_configured = False
global_gemini_model = None # 전역 Gemini 모델 인스턴스를 저장할 변수 선언

if not GEMINI_API_KEY:
    print("FATAL ERROR: GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        global_gemini_model = genai.GenerativeModel('gemini-1.5-flash') 
        print("FastAPI: Gemini API가 성공적으로 설정되고 모델이 로드되었습니다.")
        genai_configured = True
    except Exception as e:
        print(f"FastAPI: FATAL ERROR: Gemini API 구성 중 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

# --- 2. FastAPI 애플리케이션 초기화 ---
app = FastAPI(
    title="초록손 통합 AI 서비스",
    description="Gemini API를 활용한 챗봇 및 식물 진단 통합 서비스",
    version="1.0.0"
)

# --- 3. CORS 설정 ---
origins = [
    "http://localhost",
    "http://localhost:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. 이미지 및 보고서 저장 폴더 설정 및 정적 파일 서빙 ---
UPLOAD_IMAGE_DIR = "uploaded_images"
REPORT_DIR = "reports"

os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

app.mount("/uploaded_images", StaticFiles(directory=UPLOAD_IMAGE_DIR), name="uploaded_images")
app.mount("/reports_static", StaticFiles(directory=REPORT_DIR), name="reports_static")

# --- 5. 요청 데이터 모델 정의 ---
class PlantDiagnosisRequest(BaseModel):
    image_base64: str
    mime_type: str
    prompt: str
    user_id: int

# --- 6. 데이터베이스 설정 및 모델 정의 ---
DATABASE_URL = "mysql+pymysql://root:user1234@192.168.0.30:3306/greenhand" 

engine = create_engine(DATABASE_URL) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(500), nullable=False, default='')
    nickname = Column(String(50), nullable=False, default='익명')
    name = Column(String(50), nullable=False, default='이름없음')
    email = Column(String(100), unique=True, index=True, nullable=True)
    address = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', nickname='{self.nickname}')>"

class ChatLog(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    message_type = Column(String(10), nullable=False) # "user" 또는 "bot"
    message_content = Column(Text, nullable=False) # 텍스트 메시지 내용
    image_url = Column(String(255), nullable=True) # 사용자가 업로드한 이미지의 URL (Null 허용)
    file_path = Column(String(255), nullable=True) # 추가: 생성된 보고서 파일의 URL (Null 허용)
    timestamp = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ChatLog(id={self.id}, user_id={self.user_id}, message_type='{self.message_type}', timestamp='{self.timestamp}')>"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_user(db: Session, user_id: int, username: str = "default_user"):
    try:
        user = db.query(User).filter(User.user_id == user_id).one()
        print(f"Existing user found: {user}")
        return user
    except NoResultFound:
        print(f"User with user_id={user_id} not found, creating new user.")
        new_user = User(
            user_id=user_id, 
            username=username,
            password_hash='',
            nickname=f"사용자{user_id}",
            name=f"기본사용자",
            created_at=datetime.now()
        ) 
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"New user created: {new_user}")
        return new_user
    except Exception as e:
        print(f"Error getting or creating user: {type(e).__name__}: {e}")
        db.rollback()
        raise

# --- 7. 헬퍼 함수: 이미지 파일 저장 ---
async def save_base64_image(base64_string: str, mime_type: str) -> Optional[str]:
    try:
        ext = mime_type.split('/')[-1]
        if 'jpeg' in ext: ext = 'jpg'
        elif 'png' in ext: ext = 'png'
        elif 'gif' in ext: ext = 'gif'
        else: ext = 'bin'

        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_IMAGE_DIR, filename)

        image_bytes = base64.b64decode(base64_string)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return f"/uploaded_images/{filename}"
    except Exception as e:
        print(f"ERROR: Failed to save image from base64: {type(e).__name__}: {e}")
        return None

async def save_uploaded_image_file(image_file: UploadFile) -> Optional[str]:
    try:
        ext = image_file.filename.split('.')[-1] if '.' in image_file.filename else 'bin'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_IMAGE_DIR, filename)

        with open(filepath, "wb") as f:
            while contents := await image_file.read(1024 * 1024):
                f.write(contents)
        
        return f"/uploaded_images/{filename}"
    except Exception as e:
        print(f"ERROR: Failed to save uploaded image file: {type(e).__name__}: {e}")
        return None


# --- 8. 지식 데이터베이스 (농업 정보) ---
agricultural_knowledge_base = {
    "상추 재배 방법": "상추는 서늘하고 햇볕이 잘 드는 곳에서 잘 자랍니다. 씨앗을 심고 싹이 나면 솎아주세요. 물은 흙이 마르지 않게 꾸준히 주는 것이 중요합니다.",
    "토마토 병충해": "토마토에 흔한 병충해로는 탄저병, 역병, 온실가루이 등이 있습니다. 각 병충해에 맞는 방제법을 사용해야 합니다.",
    "딸기 수확 시기": "딸기는 보통 4월에서 6월 사이에 수확하며, 품종과 재배 환경에 따라 달라질 수 있습니다.",
    "스마트팜이란?": "스마트팜은 정보통신기술(ICT)을 활용하여 작물 생육 환경을 원격 및 자동으로 제어하는 농업 시스템입니다.",
    "온도 조절 중요성": "작물 생육에 있어 온도는 매우 중요합니다. 너무 높거나 낮은 온도는 작물의 스트레스를 유발하고 성장을 저해할 수 있습니다.",
    "질병 진단 기능": "식물 잎사귀 이미지를 업로드하면 질병 또는 해충을 진단해 드립니다. [질병 진단 바로가기](/PRH-002)",
    "시뮬레이션 기능": "재배할 농작물 종류를 선택하고 환경 조건(온도, 습도, 일조량 등)을 입력하면 미래 생육 상태(예상 수확량, 성장 곡선)를 예측하여 시각화해야 한다. [농작물 시뮬레이션 바로가기](/PRH-003)",
    "내 농장 확인": "현재 키우시는 작물의 성장 진행도를 한 눈에 확인하고 관리할 수 있습니다. [내 농장 바로가기](/my_farm_page_id)",
    "엑셀 보고서": "엑셀 보고서 생성을 요청하셨습니다. 'generate_excel_report' 함수를 호출합니다.",
    "워드 보고서": "워드 보고서 생성을 요청하셨습니다. 'generate_word_report' 함수를 호출합니다."
}

# --- 9. 보고서/엑셀 생성 함수 ---
# 엑셀 보고서를 생성하고, 저장된 파일의 URL (정적 서빙 경로)을 반환합니다.
# 엑셀은 정형 데이터가 없으면 의미가 없기 때문에, 데이터 없이 경고 메시지만 담음
def generate_excel_report(subject: str = "농작물", content_for_report=None): 
    try:
        # 엑셀 보고서는 정형 데이터가 필요하므로, 사용자 요청 텍스트에서 데이터를 추출하는 로직이 필요합니다.
        # 현재는 이 기능을 구현하지 않으므로, 안내 메시지만 제공합니다.
        file_base_name = f"{subject}_관련_정보_요약"
        file_name = os.path.join(REPORT_DIR, f"{file_base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        # 빈 엑셀 파일을 생성하거나, 데이터 없이 특정 메시지만 포함하는 방식도 가능
        # 여기서는 단순히 생성 안내 메시지만 반환하고, 실제 엑셀 파일은 비어있을 수 있습니다.
        # 만약 진짜 엑셀 파일을 원하면, 판다스 DataFrame을 생성해야 합니다.
        # 예: df = pd.DataFrame({'안내': ["엑셀 보고서는 데이터를 기반으로 합니다."], '내용': ["현재는 데이터 추출 기능이 제한되어 있어 워드 보고서가 더 적합합니다."]})
        # df.to_excel(file_name, index=False)
        
        # 실제 파일을 생성하지 않고 메시지만 반환하거나, 빈 파일 생성 후 메시지 추가
        # 여기서는 파일은 생성하되, 데이터는 포함하지 않는다는 메시지를 명확히 전달
        # 빈 엑셀 파일 생성
        pd.DataFrame().to_excel(file_name, index=False) # 빈 데이터프레임으로 빈 엑셀 파일 생성

        message = (
            f"요청하신 엑셀 보고서 '{os.path.basename(file_name)}'가 성공적으로 생성되었습니다."
            f"\n하지만 엑셀 보고서는 표 형식의 데이터를 기반으로 하므로, "
            f"현재 시스템에서는 **주요 정보 요약(텍스트)만 포함되어 있거나, 데이터가 비어 있을 수 있습니다.**"
            f"\n상세한 텍스트 정보는 워드 보고서로 요청하시는 것을 추천합니다."
        )

        return {"message": message, "file_path": f"/reports_static/{os.path.basename(file_name)}"}
    except Exception as e:
        print(f"Error generating excel report: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"엑셀 보고서 생성 중 예기치 않은 오류 발생: {e}")

def generate_word_report(subject: str = "농작물", content_for_report=None):
    try:
        document = Document()
        document.add_heading(f'{subject} 정보 보고서', level=1)
        document.add_paragraph(f'생성 날짜: {datetime.now().strftime("%Y년 %m월 %d일")}')
        
        if content_for_report:
            document.add_heading('1. 요청하신 정보 요약', level=2)
            # HTML 태그 (<a href> 등)를 제거하고 순수 텍스트만 넣도록 수정
            clean_content = re.sub(r'<a href=".*?\" class="link-button".*?>(.*?)</a>', r'\1', content_for_report)
            for paragraph in clean_content.split('\n'):
                if paragraph.strip():
                    document.add_paragraph(paragraph.strip())
        else:
            document.add_heading('1. 일반 농작물 정보', level=2)
            document.add_paragraph('이 보고서는 요청하신 내용에 대한 일반적인 정보를 포함합니다.')
            document.add_paragraph('구체적인 정보는 챗봇과의 대화 기록을 참고하시거나, 질문 시 더 자세히 말씀해주세요.')
            
        # "2. 참고 데이터 (샘플)" 섹션 제거
        # document.add_heading('2. 참고 데이터 (샘플)', level=2)
        # data = {} ... (이전 샘플 데이터 및 표 생성 로직 제거)
        # document.add_paragraph('\n본 보고서의 데이터는 예시이며, 실제 재배 데이터와는 다를 수 있습니다.')

        file_name = os.path.join(REPORT_DIR, f"{subject}_정보_보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        document.save(file_name)
        
        message = f"요청하신 워드 보고서 '{os.path.basename(file_name)}'가 성공적으로 생성되었습니다."
        return {"message": message, "file_path": f"/reports_static/{os.path.basename(file_name)}"}
    except ImportError:
        print("Error: 'python-docx' library not installed. Please run 'pip install python-docx'.")
        raise HTTPException(status_code=500, detail="docx 라이브러리가 설치되지 않았습니다. 'pip install python-docx'를 실행하여 설치해주세요.")
    except Exception as e:
        print(f"Error generating word report: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"워드 보고서 생성 중 예기치 않은 오류 발생: {e}")


# --- 10. API 엔드포인트 정의 ---
@app.post("/chatbot/ask")
async def ask_chatbot_endpoint(
    user_query: str = Form(""),
    user_id: int = Form(...),
    image_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if not genai_configured or global_gemini_model is None:
        print("ERROR: Gemini API not configured or model not loaded.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    if not user_query and not image_file:
        raise HTTPException(status_code=400, detail="텍스트 메시지나 이미지를 제공해야 합니다.")

    image_url_for_db = None

    if image_file:
        image_url_for_db = await save_uploaded_image_file(image_file)
        if not image_url_for_db:
            print(f"WARNING: User {user_id} uploaded image but failed to save it locally.")
            
    try:
        user = get_or_create_user(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 정보를 처리하는 중 오류가 발생했습니다: {type(e).__name__}: {e}")

    bot_response_content = ""
    bot_file_path = None
    
    # 챗봇의 마지막 일반 응답 메시지를 가져옵니다.
    last_bot_general_response_content = None
    try:
        last_general_bot_log = db.query(ChatLog)\
                                 .filter(ChatLog.user_id == user_id, 
                                         ChatLog.message_type == "bot",
                                         ChatLog.file_path == None)\
                                 .order_by(ChatLog.timestamp.desc())\
                                 .first()
        if last_general_bot_log:
            last_bot_general_response_content = last_general_bot_log.message_content
            print(f"DEBUG: Last bot general response content: {last_bot_general_response_content[:50]}...")
    except Exception as e:
        print(f"WARNING: Could not retrieve last general bot message from DB: {e}")

    # --- 보고서/엑셀 생성 요청 처리 ---
    # 1. 명시적으로 '워드' 또는 '엑셀' 키워드가 포함된 보고서 생성 요청
    is_explicit_excel_request = ("엑셀" in user_query or "excel" in user_query) and any(kw in user_query for kw in ["생성", "만들어", "정리", "파일", "줘", "보고서"])
    is_explicit_word_request = ("워드" in user_query or "word" in user_query) and any(kw in user_query for kw in ["생성", "만들어", "파일", "줘", "보고서", "리포트"])
    
    # 1-1. 명시적인 엑셀 보고서 요청 처리
    if is_explicit_excel_request:
        print("DEBUG: Caught by explicit Excel report generation condition.")
        subject_for_report = "농작물"
        if "오이" in user_query: subject_for_report = "오이"
        elif "상추" in user_query: subject_for_report = "상추"
        
        file_result = generate_excel_report(subject=subject_for_report, content_for_report=last_bot_general_response_content)
        bot_response_content = file_result["message"]
        bot_file_path = file_result["file_path"]

    # 1-2. 명시적인 워드 보고서 요청 처리
    elif is_explicit_word_request:
        print("DEBUG: Caught by explicit Word report generation condition.")
        subject_for_report = "농작물"
        if "오이" in user_query: subject_for_report = "오이"
        elif "상추" in user_query: subject_for_report = "상추"

        file_result = generate_word_report(subject=subject_for_report, content_for_report=last_bot_general_response_content)
        bot_response_content = file_result["message"]
        bot_file_path = file_result["file_path"]
        
    # 2. '보고서' 키워드만 있고 파일 형식이 불분명한 경우 (이전 답변 내용을 기반으로 재확인)
    # 이 조건은 위 명시적 요청들보다 뒤에 오면서, 동시에 명시적 요청 키워드는 포함하지 않아야 합니다.
    # 즉, "보고서"나 "report"는 있지만, "워드"도 "엑셀"도 없는 경우.
    elif ("보고서" in user_query or "report" in user_query) and \
         not ("워드" in user_query or "word" in user_query or "엑셀" in user_query or "excel" in user_query) and \
         any(kw in user_query for kw in ["파일", "줘", "생성", "만들어", "받을", "원해", "있을까", "보여줘"]):
        
        print("DEBUG: Caught by Ambiguous report type condition, offering specific report.")
        
        if last_bot_general_response_content:
            content_preview = last_bot_general_response_content.replace('\n', ' ').strip()[:30] + "..."
            bot_response_content = (
                f"네, 보고서 파일을 드릴 수 있습니다. 방금 제가 알려드린 '{content_preview}' 내용에 대해 "
                f"**워드 파일 보고서 또는 엑셀 파일 보고서 중 어떤 형식을 원하시나요?**"
                f"\n(참고: 텍스트 정보는 워드 보고서, 표 형식의 데이터는 엑셀 보고서가 더 적합합니다.)"
            )
        else:
            bot_response_content = "**어떤 형식의 보고서를 원하시나요? 워드 파일 보고서 또는 엑셀 파일 보고서 중 선택해주세요.**"
        
    # --- 일반 챗봇 응답 처리 (보고서 요청이 아닌 경우) ---
    else: 
        print("DEBUG: Falling back to knowledge base or LLM general response.")
        found_in_knowledge_base = False
        for keyword, answer in agricultural_knowledge_base.items():
            if keyword not in ["엑셀 보고서", "워드 보고서"] and keyword in user_query:
                bot_response_content = answer
                found_in_knowledge_base = True
                break
        
        if not found_in_knowledge_base:
            parts_list = []
            if user_query:
                parts_list.append({"text": user_query})
            
            if image_url_for_db:
                local_file_path_for_gemini = os.path.join(UPLOAD_IMAGE_DIR, os.path.basename(image_url_for_db))
                if os.path.exists(local_file_path_for_gemini):
                    try:
                        with open(local_file_path_for_gemini, "rb") as f:
                            image_bytes_for_gemini = f.read()
                        mime_type_for_gemini = image_file.content_type if image_file and image_file.content_type else f"image/{local_file_path_for_gemini.split('.')[-1]}"
                        if "jpg" in mime_type_for_gemini: mime_type_for_gemini = "image/jpeg"
                        elif "jpeg" in mime_type_for_gemini: mime_type_for_gemini = "image/jpeg"
                        elif "png" in mime_type_for_gemini: mime_type_for_gemini = "image/png"
                        elif "gif" in mime_type_for_gemini: mime_type_for_gemini = "image/gif"
                        
                        parts_list.append({
                            "inline_data": {
                                "mime_type": mime_type_for_gemini,
                                "data": base64.b64encode(image_bytes_for_gemini).decode('utf-8')
                            }
                        })
                    except Exception as e:
                        print(f"ERROR: Failed to read saved image for Gemini (chatbot): {type(e).__name__}: {e}")
                else:
                    print(f"WARNING: Saved image file not found for Gemini (chatbot): {local_file_path_for_gemini}")
                    
            if not parts_list:
                raise HTTPException(status_code=400, detail="텍스트 메시지나 이미지가 필요합니다.")

            contents = [{"role": "user", "parts": parts_list}]

            print(f"DEBUG FastAPI /chatbot/ask: Calling Gemini. user_id={user_id}, image_present={bool(image_file)}, query='{user_query[:50]}...'")

            try:
                llm_response = await asyncio.to_thread(global_gemini_model.generate_content, contents)
                generated_text = llm_response.text
                bot_response_content = generated_text.strip()
            except InvalidArgument as e:
                print(f"ERROR FastAPI /chatbot/ask: Gemini Invalid Argument: {e}. Contents: {contents}")
                raise HTTPException(status_code=400, detail=f"AI 모델에 전달된 인자가 유효하지 않습니다. 상세: {str(e)}")
            except ResourceExhausted as e:
                print(f"ERROR FastAPI /chatbot/ask: Gemini Resource Exhausted: {e}")
                raise HTTPException(status_code=429, detail=f"AI 모델 호출 할당량이 소진되었습니다. 잠시 후 다시 시도해주세요. 상세: {str(e)}")
            except GoogleAPIError as e:
                print(f"ERROR FastAPI /chatbot/ask: Google API Error: {type(e).__name__}: {e}")
                raise HTTPException(status_code=500, detail=f"Google AI API 통신 중 오류 발생: {str(e)}")
            except Exception as e:
                print(f"ERROR FastAPI /chatbot/ask: Unexpected error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                bot_response_content = f"죄송합니다. AI 응답 생성 중 오류가 발생했습니다: {str(e)}"

        markdown_link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
        def replace_link_with_html(match):
            link_text = match.group(1)
            link_id = match.group(2)

            mapped_file = ""
            if link_id == "/PRH-002":
                mapped_file = "imgdiagnostics/img.html"
            elif link_id == "/PRH-003":
                mapped_file = "2.html"
            elif link_id == "/my_farm_page_id":
                mapped_file = "main/main.html"
            else:
                mapped_file = "main/main.html"

            return f'<a href="../{mapped_file}" class="link-button" onclick="event.preventDefault(); window.location.href=\'../{mapped_file}\'">{link_text}</a>'

        bot_response_content = markdown_link_pattern.sub(replace_link_with_html, bot_response_content)


    # 3. 사용자 메시지 (및 이미지 URL)를 DB에 기록 (항상 가장 먼저 기록)
    try:
        user_log = ChatLog(user_id=user_id, message_type="user", message_content=user_query, image_url=image_url_for_db, timestamp=datetime.now())
        db.add(user_log)
        db.commit()
        db.refresh(user_log)

        # 8. 챗봇 응답을 DB에 기록 (bot_response_content가 비어있지 않은 경우에만 기록)
        if bot_response_content.strip():
            bot_log = ChatLog(user_id=user_id, message_type="bot", 
                              message_content=bot_response_content, 
                              image_url=None, 
                              file_path=bot_file_path,
                              timestamp=datetime.now())
            db.add(bot_log)
            db.commit()
            db.refresh(bot_log)
    except Exception as e:
        db.rollback()
        print(f"Failed to log messages to DB: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 기록 중 오류 발생: {e}")

    # 9. 클라이언트(Spring Boot)에 반환할 데이터 구성
    return {"response": bot_response_content, "file_path": bot_file_path, "image_url": image_url_for_db}


@app.post("/diagnose/plant")
async def diagnose_plant_with_gemini(request: PlantDiagnosisRequest):
    print(f"DEBUG FastAPI /diagnose/plant: Request received. user_id={request.user_id}, mime_type={request.mime_type}, prompt='{request.prompt[:50]}...'")

    if not genai_configured or global_gemini_model is None:
        print("ERROR: Gemini API not configured or model not loaded.")
        raise HTTPException(status_code=503, detail="AI 서비스가 준비되지 않았습니다. API 키를 확인하세요.")

    if not request.image_base64 or not request.mime_type.startswith("image/"):
        print("ERROR: Invalid image data received for /diagnose/plant. base64 present:", bool(request.image_base64), "mime_type:", request.mime_type)
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 필요합니다.")
        
    try:
        parts_list = [
            {"text": request.prompt},
            {
                "inline_data": {
                    "mime_type": request.mime_type,
                    "data": request.image_base64
                }
            }
        ]
        contents = [{"role": "user", "parts": parts_list}]

        print(f"DEBUG FastAPI /diagnose/plant: Calling Gemini API with contents: {contents}")

        response = await asyncio.to_thread(global_gemini_model.generate_content, contents)
        
        diagnosis_result_text = response.text
        
        print(f"DEBUG FastAPI /diagnose/plant: Gemini response for user {request.user_id}: {diagnosis_result_text[:100]}...")

        return {"response": diagnosis_result_text}

    except InvalidArgument as e:
        print(f"ERROR FastAPI /diagnose/plant: Gemini Invalid Argument: {e}. Contents: {contents}")
        raise HTTPException(status_code=400, detail=f"AI 모델에 전달된 인자가 유효하지 않습니다. 상세: {str(e)}")
    except ResourceExhausted as e:
        print(f"ERROR FastAPI /diagnose/plant: Gemini Resource Exhausted: {e}")
        raise HTTPException(status_code=429, detail=f"AI 모델 호출 할당량이 소진되었습니다. 잠시 후 다시 시도해주세요. 상세: {str(e)}")
    except GoogleAPIError as e:
        print(f"ERROR FastAPI /diagnose/plant: Google API Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Google AI API 통신 중 오류 발생: {str(e)}")
    except Exception as e:
        print(f"ERROR FastAPI /diagnose/plant: Unexpected error during Gemini call: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"식물 진단 중 오류 발생: {str(e)}. 상세 오류: {type(e).__name__}")


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
        raise HTTPException(status_code=403, detail="Forbidden file path. Only 'uploaded_images' or 'reports_static' paths are allowed.")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
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


@app.get("/chatbot/history/{user_id}", response_model=list[dict])
async def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    try:
        results = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp.asc()).all()
        
        history_list = []
        user_message_buffer = None 

        for log in results:
            if log.message_type == 'user':
                user_message_buffer = {
                    "user_query": log.message_content, 
                    "bot_response": "응답 없음", 
                    "timestamp": log.timestamp.isoformat(), 
                    "image_url": log.image_url,
                    "file_path": None
                }
            elif log.message_type == 'bot' and user_message_buffer:
                user_message_buffer["bot_response"] = log.message_content
                user_message_buffer["file_path"] = log.file_path
                history_list.append(user_message_buffer)
                user_message_buffer = None
            
        if user_message_buffer:
            history_list.append(user_message_buffer)

        return history_list
    except Exception as e:
        print(f"Error fetching chat history for user_id {user_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"이전 질문 내역을 불러오는 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    Base.metadata.create_all(bind=engine) 
    print("Database tables created/checked.")

    db = SessionLocal()
    try:
        get_or_create_user(db, user_id=1, username="default_test_user") 
    finally:
        db.close()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)