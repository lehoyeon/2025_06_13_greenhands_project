from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key'
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://root:user1234@192.168.0.30:3306/greenhand'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Crop(db.Model):
    __tablename__ = 'crops'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

API_KEY = "AIzaSyDj3yc9Ep-viuCGbttZm0R5xf7dWzY-7yQ"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

def clean_text(text: str) -> str:
    return re.sub(r"\*\*", "", text).strip()

def call_gemini_api(prompt_text):
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        return clean_text(raw_text)
    return f"Error: {response.status_code}"

@app.route("/recommend", methods=["POST"])
def recommend_crops():
    data = request.get_json()
    harvest = data.get("harvest_period")
    region = data.get("region")
    scale = data.get("scale")

    prompt = f"""
    당신은 농업 전문가입니다.
    다음 조건에 적합한 작물 5가지를 추천해 주세요.
    - 재배 희망 시기: {harvest}개월 후
    - 지역: {region}
    - 재배 규모: {scale}
    각 작물은 "작물이름 - 한 줄 설명" 형태로 출력해 주세요.
    """

    result = call_gemini_api(prompt)
    lines = [line.strip() for line in result.split('\n') if re.match(r"^\d+\. ", line)]
    parsed = []
    for line in lines:
        clean_line = clean_text(re.sub(r"^\d+\.\s*", "", line))
        name, desc = (clean_line.split(" - ", 1) + ["설명 없음"])[:2]
        parsed.append({"name": name.strip(), "description": desc.strip()})

    return jsonify({"success": True, "recommended": parsed[:2], "other_options": parsed[2:], "total_recommendations": len(parsed)})

@app.route("/crop/add", methods=["POST"])
def save_crop():
    data = request.get_json()
    name = data.get("name")
    desc = data.get("description")
    user_id = data.get("user_id")

    if not all([name, user_id]):
        return jsonify({"success": False, "error": "누락된 정보"}), 400

    try:
        crop = Crop(name=name, description=desc or '', user_id=user_id)
        db.session.add(crop)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/crops/<int:user_id>")
def get_user_crops(user_id):
    crops = Crop.query.filter_by(user_id=user_id).all()
    return jsonify({"success": True, "crops": [
        {"id": c.id, "name": c.name, "description": c.description, "created_at": c.created_at.isoformat()} for c in crops
    ]})

@app.route("/crop/delete/<int:crop_id>", methods=["DELETE"])
def delete_crop(crop_id):
    try:
        crop = Crop.query.get(crop_id)
        if not crop:
            return jsonify({"success": False, "error": "작물을 찾을 수 없습니다."}), 404
        db.session.delete(crop)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/guide")
def get_guide():
    seedling = request.args.get("name")
    if not seedling:
        return jsonify({"success": False, "error": "작물 이름이 필요합니다."}), 400
    prompt = f"{seedling}을 화분에 키우는 법을 상세히 설명해줘."
    guide = call_gemini_api(prompt)
    return jsonify({"success": True, "guide": guide})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
