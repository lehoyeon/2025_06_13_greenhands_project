import os
import joblib
import numpy as np
import requests
import datetime
import gradio as gr
from tensorflow.keras.models import load_model

# 저장 경로
SAVE_DIR = r"C:\ydata-profiling\2025_06_13\CropGrowthSimulation\Model"

# 지역 좌표 (nx, ny)
REGIONS = {
    "서울": (60, 127), "부산": (98, 76), "대구": (89, 90), "인천": (55, 124),
    "광주": (58, 74), "대전": (67, 100), "울산": (102, 84), "세종": (66, 103),
    "경기": (60, 120), "강원": (73, 134), "충북": (69, 107), "충남": (66, 101),
    "전북": (63, 89), "전남": (51, 67), "경북": (89, 91), "경남": (91, 77), "제주": (52, 38)
}

SERVICE_KEY = "mNHu0kXLC2NyHxcjF6iviFTt2cesq0/AKmwIk2+xyk9e31losEgoV3SUh7nJqg3J6L0PlL+VHAShP4WASIMrAw=="

def get_base_time():
    now = datetime.datetime.now()
    if now.minute < 45:
        now -= datetime.timedelta(hours=1)
    hour = now.hour
    return f"{hour:02d}00"

def get_weather(region):
    if region not in REGIONS:
        return None, f"지원하지 않는 지역: {region}"

    nx, ny = REGIONS[region]
    base_date = datetime.datetime.now().strftime("%Y%m%d")
    base_time = get_base_time()

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return None, f"API 호출 실패: {resp.status_code}"

        data = resp.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

        weather = {"T1H": 0.0, "REH": 0.0, "RN1": 0.0}
        latest_time = None

        # 가장 최신 fcstTime 찾기
        for it in items:
            fcst_time = it.get("fcstTime")
            if (latest_time is None) or (fcst_time > latest_time):
                latest_time = fcst_time

        # 최신 fcstTime의 필요한 카테고리 값 추출
        for it in items:
            if it.get("fcstTime") == latest_time:
                cat = it.get("category")
                val = it.get("fcstValue")
                if cat in weather:
                    try:
                        weather[cat] = float(val)
                    except Exception:
                        weather[cat] = 0.0

        return weather, None

    except Exception as e:
        return None, f"날씨 조회 실패: {e}"

def init_model():
    model_path = os.path.join(SAVE_DIR, "crop_dnn_model.h5")
    scaler_path = os.path.join(SAVE_DIR, "scaler.pkl")
    le_path = os.path.join(SAVE_DIR, "label_encoder.pkl")

    if os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(le_path):
        model = load_model(model_path)
        scaler = joblib.load(scaler_path)
        le = joblib.load(le_path)
        return model, scaler, le
    else:
        raise FileNotFoundError("모델 또는 스케일러, 레이블 인코더 파일이 없습니다.")

def predict_crop(region):
    try:
        weather, err = get_weather(region)
        if err:
            return f"❌ {err}", "날씨 정보 없이는 추천 불가능"

        model, scaler, le = init_model()

        # 고정값 N, P, K, ph
        N, P, K, ph = 80, 50, 60, 6.5
        temp = weather['T1H']
        hum = weather['REH']
        rain = weather['RN1']

        inp = np.array([[N, P, K, temp, hum, ph, rain]])
        inp_scaled = scaler.transform(inp)

        pred_proba = model.predict(inp_scaled)[0]
        pred_class_index = np.argmax(pred_proba)
        pred_label = le.inverse_transform([pred_class_index])[0]

        wt = (
            f"📊 현재 날씨 ({region})\n"
            f"🌡️ 온도: {temp}°C\n"
            f"💧 습도: {hum}%\n"
            f"🌧️ 강수량: {rain}mm"
        )
        return wt, f"🌾 추천 작물: {pred_label} (확률: {pred_proba[pred_class_index]:.2f})"

    except Exception as e:
        return f"예측 실패: {e}", ""

with gr.Blocks(css="""
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&display=swap');
    body, button, input, textarea {
        font-family: 'Nanum Gothic', 'Malgun Gothic', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
    }
""") as demo:
    gr.Markdown("# 🌾 농작물 추천 시스템")
    reg = gr.Dropdown(list(REGIONS.keys()), label="지역 선택", value="서울")
    btn = gr.Button("추천 받기")
    wout = gr.Textbox(label="날씨 정보", lines=4)
    cout = gr.Textbox(label="추천 결과", lines=4)
    btn.click(predict_crop, inputs=reg, outputs=[wout, cout])

if __name__ == "__main__":
    demo.launch(share=True)
