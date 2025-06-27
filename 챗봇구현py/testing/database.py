# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
import logging
from fastapi import HTTPException # get_or_create_user에서 HTTPException을 사용하기 위해 임포트

from config import DATABASE_URL # config.py에서 DATABASE_URL 임포트

logger = logging.getLogger(__name__) # 각 모듈에서 로거 인스턴스를 가져와 사용

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DB 모델 정의
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

# DB 세션 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 사용자 조회 또는 생성
def get_or_create_user(db: Session, user_id: int, username: str = "default_user"):
    try:
        user = db.query(User).filter(User.user_id == user_id).one()
        logger.info(f"Existing user found: {user}")
        return user
    except NoResultFound:
        logger.info(f"User with user_id={user_id} not found, creating new user.")
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
        logger.info(f"New user created: {new_user}")
        return new_user
    except Exception as e:
        logger.error(f"Error getting or creating user: {type(e).__name__}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 정보를 처리하는 중 오류가 발생했습니다: {e}")