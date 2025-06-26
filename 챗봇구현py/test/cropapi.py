import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# 환경 변수에서 API 키를 가져옵니다. 실제 배포 시에는 이렇게 사용하는 것이 좋습니다.
# 개발/테스트를 위해 여기서는 제공된 키를 사용하지만, 실제 환경에서는 보안을 위해 환경 변수를 사용하세요.
API_KEY = "AIzaSyDj3yc9Ep-viuCGbttZm0R5xf7dWzY-7yQ" # 이 키는 예시이며, 실제 키로 대체해야 합니다.
if not API_KEY:
    # API 키가 설정되지 않았을 경우 오류를 발생시킵니다.
    raise RuntimeError("GOOGLE_API_KEY 환경 변수를 설정하거나 코드를 업데이트하여 유효한 API 키를 사용해야 합니다.")

# gemini-2.0-flash 모델의 API URL로 업데이트
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

@app.route("/api/recommend-crop", methods=["POST"])
def recommend_crop():
    """
    수확 희망 시기와 재배 장소에 따라 작물을 추천합니다.
    응답은 JSON 배열 형식으로 작물 정보(이름, 화분 크기, 물의 양, 토양 유형, 난이도)를 반환합니다.
    """
    data = request.get_json()
    harvest = data.get("harvest", "")
    environment = data.get("environment", "")

    prompt_text = (
        f"수확 희망 시기: {harvest}, 재배 장소: {environment}에 적합한 작물을 추천하세요."
        " 각 작물에 대해 이름, 화분 크기, 물의 양, 토양 유형, 재배 난이도를 포함합니다."
    )

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING", "description": "작물 이름"},
                        "pot_size": {"type": "STRING", "description": "권장 화분 크기"},
                        "water_amount": {"type": "STRING", "description": "권장 물의 양"},
                        "soil_type": {"type": "STRING", "description": "권장 토양 유형"},
                        "difficulty": {"type": "STRING", "description": "재배 난이도 (예: '하', '중', '상')"}
                    },
                    "required": ["name", "pot_size", "water_amount", "soil_type", "difficulty"]
                }
            },
            "temperature": 0.3,
            "maxOutputTokens": 512,
            "topP": 0.8,
            "topK": 40
        }
    }

    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=body)
        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킵니다.
        res_json = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Gemini API 호출 실패 (recommend-crop): {e}")
        return jsonify({"error": "API 호출 실패", "detail": str(e)}), 500
    except json.JSONDecodeError as e:
        logging.error(f"API 응답 JSON 디코딩 실패 (recommend-crop): {e}")
        return jsonify({"error": "API 응답 JSON 디코딩 실패", "detail": str(e), "raw_response": response.text}), 500
    except Exception as e:
        logging.error(f"알 수 없는 오류 발생 (recommend-crop): {e}")
        return jsonify({"error": "알 수 없는 오류", "detail": str(e)}), 500

    print("Gemini API 응답 전체 (recommend-crop):", json.dumps(res_json, ensure_ascii=False, indent=2))

    try:
        if (res_json and "candidates" in res_json and len(res_json["candidates"]) > 0 and
                "content" in res_json["candidates"][0] and
                "parts" in res_json["candidates"][0]["content"] and
                len(res_json["candidates"][0]["content"]["parts"]) > 0 and
                "text" in res_json["candidates"][0]["content"]["parts"][0]):
            
            output_json_string = res_json["candidates"][0]["content"]["parts"][0]["text"]
            crops = json.loads(output_json_string) # JSON 문자열을 파싱합니다.

            # 추가된 유효성 검사: 파싱된 결과가 실제로 배열인지 확인
            if not isinstance(crops, list):
                raise TypeError("API 응답이 예상된 JSON 배열 형식이 아닙니다.")

        else:
            raise ValueError("예상치 못한 Gemini API 응답 구조 또는 내용 누락")

    except json.JSONDecodeError as e:
        logging.error(f"응답 JSON 파싱 실패 (recommend-crop): {e}")
        return jsonify({
            "error": "응답 파싱 실패",
            "detail": str(e),
            "raw_response": res_json
        }), 500
    except TypeError as e: # 새로운 TypeError 핸들링 추가
        logging.error(f"API 응답 형식 오류 (recommend-crop): {e}")
        return jsonify({
            "error": "API 응답 형식 오류",
            "detail": str(e),
            "raw_response": res_json
        }), 500
    except ValueError as e:
        logging.error(f"응답 처리 중 값 오류 (recommend-crop): {e}")
        return jsonify({
            "error": "응답 처리 중 오류",
            "detail": str(e),
            "raw_response": res_json
        }), 500
    except Exception as e:
        logging.error(f"알 수 없는 응답 처리 오류 (recommend-crop): {e}")
        return jsonify({
            "error": "알 수 없는 응답 처리 오류",
            "detail": str(e),
            "raw_response": res_json
        }), 500

    return jsonify(crops)


@app.route("/api/crop-guide", methods=["POST"])
def crop_guide():
    """
    특정 작물에 대한 재배 가이드를 생성합니다.
    응답은 JSON 배열 형식으로 단계별 가이드를 반환합니다.
    """
    data = request.get_json()
    crop_name = data.get("crop_name", "")

    if not crop_name:
        return jsonify({"error": "작물 이름이 필요합니다."}), 400

    prompt_text = f"작물 '{crop_name}'의 재배 가이드를 단계별로 상세히 설명하세요. 각 단계는 짧고 명확하게 설명하고, 다음 JSON 배열 형식으로 출력하세요: [\"1. 첫 번째 단계 설명\", \"2. 두 번째 단계 설명\", ...]. 설명은 포함하지 마세요."

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            },
            "temperature": 0.5, # 가이드 생성은 좀 더 창의적이어도 됩니다.
            "maxOutputTokens": 1024, # 가이드가 길어질 수 있으므로 토큰을 늘립니다.
            "topP": 0.8,
            "topK": 40
        }
    }

    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=body)
        response.raise_for_status()
        res_json = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Gemini API 호출 실패 (crop-guide): {e}")
        return jsonify({"error": "API 호출 실패", "detail": str(e)}), 500
    except json.JSONDecodeError as e:
        logging.error(f"API 응답 JSON 디코딩 실패 (crop-guide): {e}")
        return jsonify({"error": "API 응답 JSON 디코딩 실패", "detail": str(e), "raw_response": response.text}), 500
    except Exception as e:
        logging.error(f"알 수 없는 오류 발생 (crop-guide): {e}")
        return jsonify({"error": "알 수 없는 오류", "detail": str(e)}), 500

    print("Gemini API 응답 전체 (crop-guide):", json.dumps(res_json, ensure_ascii=False, indent=2))

    try:
        if (res_json and "candidates" in res_json and len(res_json["candidates"]) > 0 and
                "content" in res_json["candidates"][0] and
                "parts" in res_json["candidates"][0]["content"] and
                len(res_json["candidates"][0]["content"]["parts"]) > 0 and
                "text" in res_json["candidates"][0]["content"]["parts"][0]):
            
            output_json_string = res_json["candidates"][0]["content"]["parts"][0]["text"]
            guide_steps = json.loads(output_json_string) # JSON 문자열을 파싱합니다.
            if not isinstance(guide_steps, list):
                raise TypeError("가이드 단계가 배열 형식이 아닙니다.")
        else:
            raise ValueError("예상치 못한 Gemini API 응답 구조 또는 내용 누락")

    except json.JSONDecodeError as e:
        logging.error(f"응답 JSON 파싱 실패 (crop-guide): {e}")
        return jsonify({
            "error": "응답 파싱 실패",
            "detail": str(e),
            "raw_response": res_json
        }), 500
    except ValueError as e:
        logging.error(f"응답 처리 중 값 오류 (crop-guide): {e}")
        return jsonify({
            "error": "응답 처리 중 오류",
            "detail": str(e),
            "raw_response": res_json
        }), 500
    except TypeError as e:
        logging.error(f"가이드 단계 형식 오류 (crop-guide): {e}")
        return jsonify({
            "error": "가이드 단계 형식 오류",
            "detail": str(e),
            "raw_response": res_json
        }), 500
    except Exception as e:
        logging.error(f"알 수 없는 응답 처리 오류 (crop-guide): {e}")
        return jsonify({
            "error": "알 수 없는 응답 처리 오류",
            "detail": str(e),
            "raw_response": res_json
        }), 500

    return jsonify(guide_steps)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

