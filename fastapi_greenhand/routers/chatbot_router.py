# routers/chatbot_router.py
import logging
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func # func 임포트 추가 (필요시)

from database import get_db, get_or_create_user, ChatLog
from services.ai_service import get_gemini_response_for_chat, save_uploaded_image_file
from services.report_service import generate_excel_report, generate_word_report
from knowledge_base import agricultural_knowledge_base # 지식 기반 임포트

router = APIRouter()

@router.post("/ask")
async def ask_chatbot_endpoint(
    user_query: str = Form(""),
    user_id: int = Form(...),
    image_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not user_query and not image_file:
        raise HTTPException(status_code=400, detail="텍스트 메시지나 이미지를 제공해야 합니다.")

    image_url_for_db = None
    if image_file:
        image_url_for_db = await save_uploaded_image_file(image_file)
        if not image_url_for_db:
            logging.warning(f"User {user_id} uploaded image but failed to save it locally.")
            
    try:
        user = get_or_create_user(db, user_id)
    except HTTPException as e:
        raise e 
    except Exception as e:
        logging.error(f"Error processing user information: {type(e).__name__}: {e}")
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
            logging.debug(f"Last bot general response content: {last_bot_general_response_content[:50]}...")
    except Exception as e:
        logging.warning(f"Could not retrieve last general bot message from DB: {e}")

    is_explicit_excel_request = ("엑셀" in user_query or "excel" in user_query) and any(kw in user_query for kw in ["생성", "만들어", "정리", "파일", "줘", "보고서"])
    is_explicit_word_request = ("워드" in user_query or "word" in user_query) and any(kw in user_query for kw in ["생성", "만들어", "파일", "줘", "보고서", "리포트"])
    
    if is_explicit_excel_request:
        logging.info("Caught by explicit Excel report generation condition.")
        subject_for_report = "농작물"
        if "오이" in user_query: subject_for_report = "오이"
        elif "상추" in user_query: subject_for_report = "상추"
        
        file_result = generate_excel_report(subject=subject_for_report, content_for_report=last_bot_general_response_content)
        bot_response_content = file_result["message"]
        bot_file_path = file_result["file_path"]

    elif is_explicit_word_request:
        logging.info("Caught by explicit Word report generation condition.")
        subject_for_report = "농작물"
        if "오이" in user_query: subject_for_report = "오이"
        elif "상추" in user_query: subject_for_report = "상추"

        file_result = generate_word_report(subject=subject_for_report, content_for_report=last_bot_general_response_content)
        bot_response_content = file_result["message"]
        bot_file_path = file_result["file_path"]
        
    elif ("보고서" in user_query or "report" in user_query) and \
        not (is_explicit_word_request or is_explicit_excel_request) and \
        any(kw in user_query for kw in ["파일", "줘", "생성", "만들어", "받을", "원해", "있을까", "보여줘"]):
        
        logging.info("Caught by Ambiguous report type condition, offering specific report.")
        
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
        logging.info("Falling back to knowledge base or LLM general response.")
        found_in_knowledge_base = False
        
        for keyword, data in agricultural_knowledge_base.items():
            if keyword not in ["엑셀 보고서", "워드 보고서"] and keyword in user_query:
                bot_response_content = data["details"] # 지식 베이스의 상세 내용을 사용
                found_in_knowledge_base = True
                
                # Spring Boot가 처리할 수 있도록, 링크는 별도의 필드에 추가 정보로 넣습니다.
                # 또는 단순히 텍스트에 포함된 마크다운 링크 자체를 그대로 반환합니다.
                # 여기서는 텍스트에 이미 마크다운 링크가 포함되어 있으므로 추가 처리 불필요
                break
        
        if not found_in_knowledge_base:
            bot_response_content = await get_gemini_response_for_chat(user_query, image_url_for_db)

    # 사용자 메시지 (및 이미지 URL)를 DB에 기록 (항상 가장 먼저 기록)
    try:
        user_log = ChatLog(user_id=user_id, message_type="user", message_content=user_query, image_url=image_url_for_db, timestamp=datetime.now())
        db.add(user_log)
        db.commit()
        db.refresh(user_log)

        # 챗봇 응답을 DB에 기록
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
        logging.error(f"Failed to log messages to DB: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 기록 중 오류 발생: {e}")

    # 여기서는 "file_path"와 "image_url"이 "response"와 함께 반환됩니다.
    # Spring Boot에서 이 JSON 응답을 받아서 "file_path"나 "image_url"이 존재하면
    # 그에 맞는 UI (다운로드 버튼, 이미지 표시 등)를 추가로 렌더링해야 합니다.
    return {"response": bot_response_content, "file_path": bot_file_path, "image_url": image_url_for_db}


@router.get("/history/{user_id}", response_model=list[dict])
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
        logging.error(f"Error fetching chat history for user_id {user_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"이전 질문 내역을 불러오는 중 오류가 발생했습니다: {e}")