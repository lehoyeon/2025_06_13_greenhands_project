from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
from datetime import datetime
import json
import logging
from typing import Dict, Any, List, Optional

# config.py의 DATABASE_URL을 사용
from config import DATABASE_URL

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
    image_url = Column(String(255), nullable=True) # 사용자가 업로드한 이미지 또는 봇 응답 이미지 URL
    file_path = Column(String(255), nullable=True) # 생성된 보고서 파일 URL
    link_url = Column(String(255), nullable=True) # 챗봇 응답 내 링크 URL
    timestamp = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ChatLog(id={self.id}, user_id={self.user_id}, message_type='{self.message_type}', timestamp='{self.timestamp}')>"

class ImgLog(Base): # 식물 진단 기록 테이블
    __tablename__ = "img_logs" 
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False) # users 테이블과 연결
    diagnosed_at = Column(DateTime, default=datetime.now) # 진단 시각
    image_url = Column(String(255)) # 진단 이미지 경로
    diagnosis_result = Column(String(500)) # 진단 결과 요약 
    diagnosis_details = Column(Text, nullable=True) # 상세 진단 내용
    severity = Column(String(50), nullable=True) # 심각도
    plant_name = Column(String(100), nullable=True) # 진단된 작물명

    def __repr__(self):
        return f"<ImgLog(id={self.id}, user_id={self.user_id}, diagnosed_at='{self.diagnosed_at}')>"

# 새로운 user_crops 테이블 모델 (재배 리스트)
class UserCropNew(Base):
    __tablename__ = "user_crops_new" 
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False) # users 테이블과 연결, user_id는 String으로 유지 (DB 타입 맞춤)
    crop_id_from_kb = Column(String(50), nullable=False) # knowledge_base.py의 작물 ID 저장용
    crop_name = Column(String(100), nullable=False) # 작물 실제 이름
    nick_name = Column(String(100), nullable=True) # 사용자가 지정한 별칭

    environment = Column(String(50), nullable=True) 
    difficulty = Column(String(10), nullable=True) 
    pot_size = Column(String(50), nullable=True) 
    water_amount = Column(String(50), nullable=True) 
    soil_type = Column(String(50), nullable=True) 
    pest_control_info = Column(Text, nullable=True) # 병충해 관리 정보
    thumbnail_image = Column(String(255), nullable=True) 

    growth_stage = Column(String(50), nullable=True, default='초기')
    care_instruction = Column(Text, nullable=True) # JSON 문자열로 상세 가이드 저장
    other_notes = Column(Text, nullable=True)
    crop_status = Column(Enum('NONE', 'GROWING', 'HARVESTED', 'DIED', name='crop_status_enum'), default='NONE')
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserCropNew(id={self.id}, user_id='{self.user_id}', crop_name='{self.crop_name}', nick_name='{self.nick_name}')>"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_user(db: Session, user_id: int, username: str = "default_user"):
    try:
        user = db.query(User).filter(User.user_id == user_id).one()
        logging.info(f"Existing user found: {user}")
        return user
    except NoResultFound:
        logging.info(f"User with user_id={user_id} not found, creating new user.")
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
        logging.info(f"New user created: {new_user}")
        return new_user
    except Exception as e:
        logging.error(f"Error getting or creating user: {type(e).__name__}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 정보를 처리하는 중 오류가 발생했습니다: {e}")


def add_user_crop(
    db: Session, 
    user_id: int, 
    crop_data: Dict[str, Any], 
    alias: Optional[str] = None
):
    care_instruction_json = json.dumps(crop_data.get("detailed_guide", {}), ensure_ascii=False)

    new_user_crop = UserCropNew( 
        user_id=str(user_id), 
        crop_id_from_kb=crop_data.get("id"), 
        crop_name=crop_data.get("name"),
        nick_name=alias if alias else crop_data.get("name"),
        
        environment=crop_data.get("cultivation_location")[0] if crop_data.get("cultivation_location") and len(crop_data.get("cultivation_location")) > 0 else None,
        difficulty=crop_data.get("difficulty"),
        pot_size=crop_data.get("pot_size"),
        water_amount=crop_data.get("water_amount"),
        soil_type=crop_data.get("soil_type"),
        pest_control_info=crop_data.get("pest_control", "정보 없음"),
        thumbnail_image=crop_data.get("thumbnail_image"),

        growth_stage="초기",
        care_instruction=care_instruction_json,
        other_notes="",
        crop_status="NONE",
        
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_user_crop)
    db.commit()
    db.refresh(new_user_crop)
    return new_user_crop

def get_user_crops(db: Session, user_id: int) -> List['UserCropNew']: 
    return db.query(UserCropNew).filter(UserCropNew.user_id == str(user_id)).all()

def delete_user_crop(db: Session, user_id: int, user_crop_id: int):
    crop_to_delete = db.query(UserCropNew).filter( 
        UserCropNew.user_id == str(user_id),
        UserCropNew.id == user_crop_id 
    ).first()
    
    if crop_to_delete:
        db.delete(crop_to_delete)
        db.commit()
        return True
    return False

def delete_all_user_crops(db: Session, user_id: int):
    db.query(UserCropNew).filter(UserCropNew.user_id == str(user_id)).delete()
    db.commit()
    return True