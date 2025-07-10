# database.py 파일

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
    link_url = Column(String(255), nullable=True) # ⭐ 추가된 컬럼: 챗봇 응답 내 링크 URL
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
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    crop_id_from_kb = Column(String(50), nullable=False)
    crop_name = Column(String(100), nullable=False)
    nick_name = Column(String(100), nullable=True)

    environment = Column(String(50), nullable=True)
    difficulty = Column(String(10), nullable=True)
    pot_size = Column(String(50), nullable=True)
    water_amount = Column(String(50), nullable=True)
    soil_type = Column(String(50), nullable=True)
    pest_control_info = Column(Text, nullable=True)
    thumbnail_image = Column(String(255), nullable=True)

    growth_stage = Column(String(50), nullable=True, default='파종')
    progress_percent = Column(Integer, nullable=False, default=0)
    last_photo_uploaded_at = Column(DateTime, nullable=True)
    growth_stage_start_date = Column(DateTime, nullable=True)
    expected_cultivation_days = Column(Integer, nullable=True)

    care_instruction = Column(Text, nullable=True)
    other_notes = Column(Text, nullable=True)
    crop_status = Column(Enum('NONE', 'GROWING', 'HARVESTED', 'DIED', name='crop_status_enum'), default='NONE')

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_main_crop = Column(Boolean, default=False, nullable=False)


    def __repr__(self):
        return f"<UserCropNew(id={self.id}, user_id='{self.user_id}', crop_name='{self.crop_name}', nick_name='{self.nick_name}', growth_stage='{self.growth_stage}', progress_percent={self.progress_percent}, is_main_crop={self.is_main_crop})>"


# ⭐⭐ UserCropHarvested 모델에 expected_cultivation_days 컬럼 추가 ⭐⭐
class UserCropHarvested(Base):
    __tablename__ = "user_crops_harvested"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    crop_id_from_kb = Column(String(50), nullable=False)
    crop_name = Column(String(100), nullable=False)
    nick_name = Column(String(100), nullable=True)

    environment = Column(String(50), nullable=True)
    difficulty = Column(String(10), nullable=True)
    pot_size = Column(String(50), nullable=True)
    water_amount = Column(String(50), nullable=True)
    soil_type = Column(String(50), nullable=True)
    pest_control_info = Column(Text, nullable=True)
    thumbnail_image = Column(String(255), nullable=True)

    progress_percent = Column(Integer, nullable=False, default=100)
    last_photo_uploaded_at = Column(DateTime, nullable=True)
    growth_stage_start_date = Column(DateTime, nullable=True)
    growth_stage = Column(String(50), nullable=True)
    expected_cultivation_days = Column(Integer, nullable=True) # ⭐ 추가된 컬럼 ⭐

    care_instruction = Column(Text, nullable=True)
    other_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    harvested_at = Column(DateTime, nullable=False, default=func.now())
    yield_info = Column(Text, nullable=True)

    def __repr__(self):
        return f"<UserCropHarvested(id={self.id}, user_id='{self.user_id}', crop_name='{self.crop_name}', harvested_at='{self.harvested_at}')>"

# ⭐⭐ 새로 추가: UserChecklistItem 모델 ⭐⭐
class UserChecklistItem(Base):
    __tablename__ = "user_checklist_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user_crop_id = Column(Integer, ForeignKey("user_crops_new.id"), nullable=False)
    item_id = Column(String(255), nullable=False) # 체크리스트 항목 고유 ID (예: "water-123", "sunlight-abc", "guide-456-0")
    is_completed = Column(Boolean, default=False, nullable=False) # 완료 여부
    completed_at = Column(DateTime, nullable=True) # 완료 시각 (선택 사항)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserChecklistItem(id={self.id}, user_id={self.user_id}, user_crop_id={self.user_crop_id}, item_id='{self.item_id}', is_completed={self.is_completed})>"


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
        raise RuntimeError(f"사용자 정보를 처리하는 중 오류가 발생했습니다: {e}")

# ⭐⭐ add_user_crop_to_db 함수 수정 (knowledge_base에서 expected_cultivation_days 가져와 저장) ⭐⭐
def add_user_crop_to_db(
    db: Session,
    user_id: int,
    crop_kb_id: str,
    alias: Optional[str] = None,
    is_main: bool = False,
    planting_method: Optional[str] = None
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

    initial_growth_stage = '파종'
    initial_progress_percent = 0
    if planting_method == 'seedling':
        initial_growth_stage = '새싹'
        initial_progress_percent = 10
    elif planting_method == 'seed':
        initial_growth_stage = '파종'
        initial_progress_percent = 0

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

        growth_stage=initial_growth_stage,
        progress_percent=initial_progress_percent,
        growth_stage_start_date=datetime.now(),
        expected_cultivation_days=crop_data_from_kb.get("expected_cultivation_days"),

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

# ⭐⭐ activate_user_crop_in_db 함수 수정 (knowledge_base에서 expected_cultivation_days 가져와 저장) ⭐⭐
def activate_user_crop_in_db(db: Session, user_id: int, crop_kb_id: str, alias: str,
                             user_crop_db_id: Optional[int] = None,
                             is_main: Optional[bool] = None,
                             planting_method: Optional[str] = None):
    """
    사용자의 작물을 나의 농장(is_main_crop=True)으로 설정합니다.
    기존 레코드 ID (user_crop_db_id)가 제공되면 해당 레코드를 업데이트하고,
    없으면 is_main_crop=True인 새로운 레코드를 생성합니다.
    planting_method에 따라 growth_stage와 progress_percent 초기값을 설정합니다.
    """
    initial_growth_stage = '파종'
    initial_progress_percent = 0

    if planting_method == 'seedling':
        initial_growth_stage = '새싹'
        initial_progress_percent = 10
    elif planting_method == 'seed':
        initial_growth_stage = '파종'
        initial_progress_percent = 0

    from knowledge_base import get_crop_by_id
    crop_data_from_kb = get_crop_by_id(crop_kb_id)
    expected_days_from_kb = crop_data_from_kb.get("expected_cultivation_days") if crop_data_from_kb else None


    if user_crop_db_id:
        existing_crop = db.query(UserCropNew).filter(
            UserCropNew.user_id == user_id,
            UserCropNew.id == user_crop_db_id
        ).first()

        if existing_crop:
            existing_crop.nick_name = alias
            if is_main is not None:
                existing_crop.is_main_crop = is_main

            existing_crop.updated_at = datetime.now()

            if planting_method:
                existing_crop.growth_stage = initial_growth_stage
                existing_crop.progress_percent = initial_progress_percent
                existing_crop.growth_stage_start_date = datetime.now()

            existing_crop.expected_cultivation_days = expected_days_from_kb

            db.add(existing_crop)
            db.commit()
            db.refresh(existing_crop)
            logging.info(f"Updated user crop {user_crop_db_id} to main crop with alias '{alias}'.")
            return existing_crop
        else:
            logging.warning(f"User crop with ID {user_crop_db_id} not found for user {user_id}. Creating new record instead.")
            pass # continue to the creation part

    if not crop_data_from_kb:
        logging.error(f"Crop with ID {crop_kb_id} not found in knowledge base during activation.")
        return None

    care_instruction_json = json.dumps(crop_data_from_kb.get("detailed_guide", {}), ensure_ascii=False)

    new_user_crop = UserCropNew(
        user_id=user_id,
        crop_id_from_kb=crop_data_from_kb.get("id"),
        crop_name=crop_data_from_kb.get("name"),
        nick_name=alias,
        environment=crop_data_from_kb.get("cultivation_location")[0] if crop_data_from_kb.get("cultivation_location") and len(crop_data_from_kb.get("cultivation_location")) > 0 else None,
        difficulty=crop_data_from_kb.get("difficulty"),
        pot_size=crop_data_from_kb.get("pot_size"),
        water_amount=crop_data_from_kb.get("water_amount"),
        soil_type=crop_data_from_kb.get("soil_type"),
        pest_control_info=crop_data_from_kb.get("pest_control", "정보 없음"),
        thumbnail_image=crop_data_from_kb.get("thumbnail_image"),

        growth_stage=initial_growth_stage,
        progress_percent=initial_progress_percent,
        growth_stage_start_date=datetime.now(),
        expected_cultivation_days=expected_days_from_kb,

        care_instruction=care_instruction_json,
        other_notes="",
        crop_status="NONE",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_main_crop=is_main if is_main is not None else True
    )
    db.add(new_user_crop)
    db.commit()
    db.refresh(new_user_crop)
    logging.info(f"Created new user crop with ID {new_user_crop.id} as main crop.")
    return new_user_crop

# ⭐⭐ harvest_user_crop_to_db 함수 수정 (yield_info DTO에서 받아오도록 변경) ⭐⭐
def harvest_user_crop_to_db(db: Session, user_id: int, user_crop_id: int, yield_info: Optional[str] = None):
    """
    특정 작물을 수확 완료 처리하여 Harvested 테이블로 이동시킵니다.
    """
    crop_to_harvest = db.query(UserCropNew).filter(
        UserCropNew.user_id == user_id,
        UserCropNew.id == user_crop_id
    ).first()

    if not crop_to_harvest:
        logging.warning(f"UserCropNew (id={user_crop_id}, user_id={user_id}) not found for harvesting.")
        return False

    try:
        # nick_name이 None일 경우 crop_name을 기본값으로 사용
        harvested_nick_name = crop_to_harvest.nick_name if crop_to_harvest.nick_name is not None else crop_to_harvest.crop_name

        harvested_crop = UserCropHarvested(
            user_id=crop_to_harvest.user_id,
            crop_id_from_kb=crop_to_harvest.crop_id_from_kb,
            crop_name=crop_to_harvest.crop_name,
            nick_name=harvested_nick_name, # 여기서 기본값 설정 로직 추가
            environment=crop_to_harvest.environment,
            difficulty=crop_to_harvest.difficulty,
            pot_size=crop_to_harvest.pot_size,
            water_amount=crop_to_harvest.water_amount,
            soil_type=crop_to_harvest.soil_type,
            pest_control_info=crop_to_harvest.pest_control_info,
            thumbnail_image=crop_to_harvest.thumbnail_image,
            progress_percent=100, # 수확 완료 시 100%로 고정
            last_photo_uploaded_at=crop_to_harvest.last_photo_uploaded_at,
            growth_stage_start_date=crop_to_harvest.growth_stage_start_date,
            growth_stage='수확 완료', # 수확 완료 단계로 설정
            expected_cultivation_days=crop_to_harvest.expected_cultivation_days,
            care_instruction=crop_to_harvest.care_instruction,
            other_notes=crop_to_harvest.other_notes,
            created_at=crop_to_harvest.created_at,
            updated_at=datetime.now(), # 최종 업데이트 시간
            harvested_at=datetime.now(), # 수확 완료 시각
            yield_info=yield_info # 수확량 정보 (API에서 전달받음)
        )
        db.add(harvested_crop)

        db.delete(crop_to_harvest)
        db.commit()
        logging.info(f"UserCropNew (id={user_crop_id}, user_id={user_id}) successfully harvested and moved to harvested_crops.")
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Error harvesting user crop (id={user_crop_id}, user_id={user_id}): {type(e).__name__}: {e}")
        return False


def get_user_crops(db: Session, user_id: int, is_main_crop: Optional[bool] = None) -> List['UserCropNew']:
    query = db.query(UserCropNew).filter(UserCropNew.user_id == user_id)
    if is_main_crop is not None:
        query = query.filter(UserCropNew.is_main_crop == is_main_crop)
    return query.all()

# ⭐⭐ 새로 추가: 수확된 작물 조회 함수 ⭐⭐
def get_harvested_crops(db: Session, user_id: int) -> List['UserCropHarvested']:
    return db.query(UserCropHarvested).filter(UserCropHarvested.user_id == user_id).order_by(UserCropHarvested.harvested_at.desc()).all()

# ⭐⭐ 새로 추가: 체크리스트 항목 상태 업데이트 함수 ⭐⭐
def update_checklist_item_status( # ⭐ 이 함수가 존재하는지 확인! ⭐
    db: Session,
    user_id: int,
    user_crop_id: int,
    item_id: str,
    is_completed: bool
) -> Optional['UserChecklistItem']: # 타입 힌트에 문자열 사용 (아직 UserChecklistItem이 정의되기 전일 수 있으므로)

    checklist_item = db.query(UserChecklistItem).filter(
        UserChecklistItem.user_id == user_id,
        UserChecklistItem.user_crop_id == user_crop_id,
        UserChecklistItem.item_id == item_id
    ).first()

    if checklist_item:
        # 기존 항목이 있으면 업데이트
        checklist_item.is_completed = is_completed
        checklist_item.completed_at = datetime.now() if is_completed else None
        checklist_item.updated_at = datetime.now()
    else:
        # 없으면 새로 생성
        checklist_item = UserChecklistItem(
            user_id=user_id,
            user_crop_id=user_crop_id,
            item_id=item_id,
            is_completed=is_completed,
            completed_at=datetime.now() if is_completed else None
        )
        db.add(checklist_item)

    db.commit()
    db.refresh(checklist_item)
    return checklist_item

# ⭐⭐ 새로 추가: 특정 작물의 체크리스트 항목 상태 조회 함수 ⭐⭐
def get_user_checklist_items( # ⭐ 이 함수도 존재하는지 확인! ⭐
    db: Session,
    user_id: int,
    user_crop_id: int
) -> List['UserChecklistItem']: # 타입 힌트에 문자열 사용 (아직 UserChecklistItem이 정의되기 전일 수 있으므로)
    return db.query(UserChecklistItem).filter(
        UserChecklistItem.user_id == user_id,
        UserChecklistItem.user_crop_id == user_crop_id
    ).all()


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

# 스크ript 실행 시 테이블 생성 (선택 사항)
if __name__ == "__main__":
    create_db_and_tables()