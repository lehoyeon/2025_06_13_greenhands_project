# routers/chatbot_router.py
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import re
import logging
from typing import Optional

# 프로젝트 내부 모듈 임포트
from database import get_db, get_or_create_user, ChatLog
from models.chat import PlantDiagnosisRequest 
from services.gemini_service import generate_content_with_gemini, save_uploaded_image_file, get_image_parts_for_gemini
from services.report_service import generate_excel_report, generate_word_report
from services.knowledge_base import agricultural_knowledge_base, get_mapped_file_path

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chatbot/ask")
async def ask_chatbot_endpoint(
    user_query: str = Form(""),
    user_id: int = Form(...),
    image_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if not user_query and not image_file:
        raise HTTPException(status_code=400, detail="텍스트 메시지나 이미지를 제공해야 합니다.")

    image_url_for_db = None
    if image_file:
        image_url_for_db = await save_uploaded_image_file(image_file)
        if not image_url_for_db:
            logger.warning(f"User {user_id} uploaded image but failed to save it locally.")
            
    try:
        user = get_or_create_user(db, user_id)
    except HTTPException as e:
        raise e 
    except Exception as e:
        logger.error(f"Error processing user information: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 정보를 처리하는 중 오류가 발생했습니다: {type(e).__name__}: {e}")

    bot_response_content = ""
    bot_file_path = None
    
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
            logger.debug(f"Last bot general response content: {last_bot_general_response_content[:50]}...")
    except Exception as e:
        logger.warning(f"Could not retrieve last general bot message from DB: {e}")

    is_explicit_excel_request = ("엑셀" in user_query or "excel" in user_query) and any(kw in user_query for kw in ["생성", "만들어", "정리", "파일", "줘", "보고서"])
    is_explicit_word_request = ("워드" in user_query or "word" in user_query) and any(kw in user_query for kw in ["생성", "만들어", "파일", "줘", "보고서", "리포트"])
    
    if is_explicit_excel_request:
        logger.info("Caught by explicit Excel report generation condition.")
        subject_for_report = "농작물"
        if "오이" in user_query: subject_for_report = "오이"
        elif "상추" in user_query: subject_for_report = "상추"
        
        file_result = generate_excel_report(subject=subject_for_report, content_for_report=last_bot_general_response_content)
        bot_response_content = file_result["message"]
        bot_file_path = file_result["file_path"]

    elif is_explicit_word_request:
        logger.info("Caught by explicit Word report generation condition.")
        subject_for_report = "농작물"
        if "오이" in user_query: subject_for_report = "오이"
        elif "상추" in user_query: subject_for_report = "상추"

        file_result = generate_word_report(subject=subject_for_report, content_for_report=last_bot_general_response_content)
        bot_response_content = file_result["message"]
        bot_file_path = file_result["file_path"]
        
    elif ("보고서" in user_query or "report" in user_query) and \
          not (is_explicit_word_request or is_explicit_excel_request) and \
          any(kw in user_query for kw in ["파일", "줘", "생성", "만들어", "받을", "원해", "있을까", "보여줘"]):
        
        logger.info("Caught by Ambiguous report type condition, offering specific report.")
        
        if last_bot_general_response_content:
            content_preview = last_bot_general_response_content.replace('\n', ' ').strip()[:30] + "..."
            bot_response_content = (
                f"네, 보고서 파일을 드릴 수 있습니다. 방금 제가 알려드린 '{content_preview}' 내용에 대해 "
                f"**워드 파일 보고서 또는 엑셀 파일 보고서 중 어떤 형식을 원하시나요?**"
                f"\n(참고: 텍스트 정보는 워드 보고서, 표 형식의 데이터는 엑셀 보고서가 더 적합합니다.)"
            )
        else:
            bot_response_content = "**어떤 형식의 보고서를 원하시나요? 워드 파일 보고서 또는 엑셀 파일 보고서 중 선택해주세요.**"
        
    else: 
        logger.info("Falling back to knowledge base or LLM general response.")
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
                image_parts = await get_image_parts_for_gemini(image_url_for_db, image_file.content_type if image_file else None)
                if image_parts:
                    parts_list.append(image_parts)
                
            if not parts_list:
                raise HTTPException(status_code=400, detail="텍스트 메시지나 이미지가 필요합니다.")

            contents = [{"role": "user", "parts": parts_list}]

            logger.info(f"Calling Gemini for chatbot. user_id={user_id}, image_present={bool(image_file)}, query='{user_query[:50]}...'")

            try:
                generated_text = await generate_content_with_gemini('gemini-1.5-flash', contents)
                bot_response_content = generated_text.strip()
            except Exception as e: 
                logger.error(f"Error during Gemini call in chatbot: {e}")
                raise HTTPException(status_code=500, detail=f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}")

        markdown_link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
        def replace_link_with_html(match):
            link_text = match.group(1)
            link_id = match.group(2)
            # HTML 파일들이 루트에 있다고 가정하므로, get_mapped_file_path 결과만 사용
            mapped_file = get_mapped_file_path(link_id)
            # 주의: HTML 링크는 FastAPI의 정적 파일 서빙 경로에 맞게 조정해야 합니다.
            # 현재는 루트에 있는 파일을 가리키도록 합니다.
            return f'<a href="{mapped_file}" class="link-button" onclick="event.preventDefault(); window.location.href=\'{mapped_file}\'">{link_text}</a>'

        bot_response_content = markdown_link_pattern.sub(replace_link_with_html, bot_response_content)

    try:
        user_log = ChatLog(user_id=user_id, message_type="user", message_content=user_query, image_url=image_url_for_db, timestamp=datetime.now())
        db.add(user_log)
        db.commit()
        db.refresh(user_log)

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
        logger.error(f"Failed to log messages to DB: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 기록 중 오류 발생: {e}")

    return {"response": bot_response_content, "file_path": bot_file_path, "image_url": image_url_for_db}


@router.post("/diagnose/plant")
async def diagnose_plant_with_gemini(request: PlantDiagnosisRequest):
    logger.info(f"Request received for /diagnose/plant. user_id={request.user_id}, mime_type={request.mime_type}, prompt='{request.prompt[:50]}...'")

    if not request.image_base64 or not request.mime_type.startswith("image/"):
        logger.error(f"Invalid image data received for /diagnose/plant. base64 present: {bool(request.image_base64)}, mime_type: {request.mime_type}")
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

        logger.info(f"Calling Gemini API for plant diagnosis.")

        diagnosis_result_text = await generate_content_with_gemini('gemini-1.5-flash', contents)
        
        logger.info(f"Gemini response for user {request.user_id} (diagnose/plant): {diagnosis_result_text[:100]}...")

        return {"response": diagnosis_result_text}

    except Exception as e:
        logger.error(f"Unexpected error during Gemini call (diagnose/plant): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"식물 진단 중 오류 발생: {str(e)}. 상세 오류: {type(e).__name__}")


@router.get("/chatbot/history/{user_id}", response_model=list[dict])
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
        logger.error(f"Error fetching chat history for user_id {user_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"이전 질문 내역을 불러오는 중 오류가 발생했습니다: {e}")