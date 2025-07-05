# database.py

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
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
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False) # users 테이블과 연결, user_id는 Integer로 (User 모델과 일치시킴)
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
    is_main_crop = Column(Boolean, default=False, nullable=False) # ⭐⭐⭐ 이 줄 추가 ⭐⭐⭐

    def __repr__(self):
        return f"<UserCropNew(id={self.id}, user_id='{self.user_id}', crop_name='{self.crop_name}', nick_name='{self.nick_name}', is_main_crop={self.is_main_crop})>"

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
        from fastapi import HTTPException # 여기에서 임포트 추가
        raise HTTPException(status_code=500, detail=f"사용자 정보를 처리하는 중 오류가 발생했습니다: {e}")

def add_user_crop_to_db(
    db: Session,
    user_id: int,
    crop_kb_id: str,
    alias: Optional[str] = None,
    is_main: bool = False
):
    try:
        from knowledge_base import get_crop_by_id
        crop_data_from_kb = get_crop_by_id(crop_kb_id)
        if not crop_data_from_kb:
            logging.error(f"Crop with ID {crop_kb_id} not found in knowledge base.")
            return None
    except ImportError:
        logging.error("knowledge_base.py module not found. Please ensure it exists and has get_crop_by_id.")
        return None
    except Exception as e:
        logging.error(f"Error getting crop data from knowledge base: {e}")
        return None

    care_instruction_json = json.dumps(crop_data_from_kb.get("detailed_guide", {}), ensure_ascii=False)

    new_user_crop = UserCropNew(
        user_id=user_id,
        crop_id_from_kb=crop_data_from_kb.get("id"),
        crop_name=crop_data_from_kb.get("name"),
        nick_name=alias if alias else crop_data_from_kb.get("name"),

        environment=crop_data_from_kb.get("cultivation_location")[0] if crop_data_from_kb.get("cultivation_location") and len(crop_data_from_kb.get("cultivation_location")) > 0 else None,
        difficulty=crop_data_from_kb.get("difficulty"),
        pot_size=crop_data_from_kb.get("pot_size"),
        water_amount=crop_data_from_kb.get("water_amount"),
        soil_type=crop_data_from_kb.get("soil_type"),
        pest_control_info=crop_data_from_kb.get("pest_control", "정보 없음"),
        thumbnail_image=crop_data_from_kb.get("thumbnail_image"),

        growth_stage="초기",
        care_instruction=care_instruction_json,
        other_notes="",
        crop_status="NONE",

        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_main_crop=is_main
    )
    db.add(new_user_crop)
    db.commit()
    db.refresh(new_user_crop)
    return new_user_crop

def activate_user_crop_in_db(db: Session, user_id: int, crop_kb_id: str, alias: Optional[str]):
    """
    사용자의 특정 작물 is_main_crop을 True로 설정합니다.
    다른 작물의 is_main_crop 상태는 변경하지 않습니다.
    """
    # ⭐⭐⭐ 이 부분을 완전히 제거하여 여러 is_main_crop=True를 허용합니다. ⭐⭐⭐
    # db.query(UserCropNew).filter(
    #     UserCropNew.user_id == user_id,
    #     UserCropNew.is_main_crop == True
    # ).update({"is_main_crop": False}, synchronize_session=False)

    # 선택된 작물을 is_main_crop=True로 설정
    # 해당 user_id와 crop_kb_id, 별칭을 가진 작물이 이미 있는지 확인
    existing_crop = db.query(UserCropNew).filter(
        UserCropNew.user_id == user_id,
        UserCropNew.crop_id_from_kb == crop_kb_id,
        UserCropNew.nick_name == alias # 별칭까지 일치하는 작물을 찾습니다.
    ).first()

    if existing_crop:
        # 이미 존재하는 경우 is_main_crop만 True로 업데이트
        existing_crop.is_main_crop = True
        db.add(existing_crop) # 변경 사항을 session에 추가
        db.commit()
        db.refresh(existing_crop)
        return existing_crop
    else:
        # 존재하지 않는 경우 새로운 작물로 추가하면서 is_main_crop=True로 설정
        # 이 경우는 프론트엔드에서 기존 관심 작물을 삭제하고 새로운 is_main=True로 등록하는 흐름에 해당합니다.
        activated_crop = add_user_crop_to_db(db, user_id, crop_kb_id, alias, is_main=True)
        db.commit()
        db.refresh(activated_crop)
        return activated_crop

def get_user_crops(db: Session, user_id: int, is_main_crop: Optional[bool] = None) -> List['UserCropNew']:
    query = db.query(UserCropNew).filter(UserCropNew.user_id == user_id)
    if is_main_crop is not None:
        query = query.filter(UserCropNew.is_main_crop == is_main_crop)
    return query.all()

def delete_user_crop(db: Session, user_id: int, user_crop_id: int):
    """
    특정 사용자의 특정 작물을 데이터베이스에서 삭제합니다.
    """
    crop_to_delete = db.query(UserCropNew).filter(
        UserCropNew.user_id == user_id,
        UserCropNew.id == user_crop_id
    ).first()

    if crop_to_delete:
        db.delete(crop_to_delete)
        db.commit()
        return True
    return False

def delete_all_user_crops(db: Session, user_id: int):
    """
    특정 사용자의 모든 작물을 데이터베이스에서 삭제합니다.
    """
    db.query(UserCropNew).filter(UserCropNew.user_id == user_id).delete()
    db.commit()
    return True

# DB 초기화 및 테이블 생성 함수
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)
    logging.info("Database and tables created or already exist.")

# 스크립트 실행 시 테이블 생성 (선택 사항)
if __name__ == "__main__":
    create_db_and_tables()