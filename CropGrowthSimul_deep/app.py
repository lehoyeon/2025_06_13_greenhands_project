from flask import Flask, jsonify, render_template, Response
import os
import numpy as np
import pandas as pd
import joblib
import json
from tensorflow.keras.models import load_model
import tensorflow as tf

app = Flask(__name__)
app.jinja_env.cache = {}

# 경로 설정
SAVE_DIR = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep"
DATASET_DIR = os.path.join(SAVE_DIR, "dataset")

WEATHER_MODEL_PATH = os.path.join(SAVE_DIR, "weather_dl_model.h5")
WEATHER_SCALER_PATH = os.path.join(SAVE_DIR, "scaler_weather.pkl")
WEATHER_FEATURES_PATH = os.path.join(SAVE_DIR, "weather_features.pkl")
CROP_MODEL_PATH = os.path.join(SAVE_DIR, "crop_dnn_model.h5")
CROP_SCALER_PATH = os.path.join(SAVE_DIR, "scaler.pkl")
CROP_LE_PATH = os.path.join(SAVE_DIR, "label_encoder.pkl")


def check_file_exists(filepath, name):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"❌ {name} 파일이 없습니다: {filepath}")


def load_weather_model():
    check_file_exists(WEATHER_MODEL_PATH, "날씨 예측 모델")
    check_file_exists(WEATHER_SCALER_PATH, "날씨 스케일러")
    check_file_exists(WEATHER_FEATURES_PATH, "날씨 특성 목록")

    try:
        model = load_model(WEATHER_MODEL_PATH, compile=False)
    except Exception as e:
        print(f"❌ 날씨 모델 로드 실패: {e}")
        raise e

    scaler = joblib.load(WEATHER_SCALER_PATH)
    feature_columns = joblib.load(WEATHER_FEATURES_PATH)
    return model, scaler, feature_columns


def load_crop_model():
    check_file_exists(CROP_MODEL_PATH, "작물 추천 모델")
    check_file_exists(CROP_SCALER_PATH, "작물 스케일러")
    check_file_exists(CROP_LE_PATH, "작물 라벨 인코더")

    try:
        model = load_model(CROP_MODEL_PATH, compile=False)
    except Exception as e:
        print(f"❌ 작물 모델 로드 실패: {e}")
        raise e

    scaler = joblib.load(CROP_SCALER_PATH)
    le = joblib.load(CROP_LE_PATH)
    return model, scaler, le


def predict_weather():
    file_path = os.path.join(DATASET_DIR, "weather_2024.csv")
    check_file_exists(file_path, "날씨 데이터 CSV")

    df = pd.read_csv(file_path, encoding='cp949')

    for col in df.columns:
        if '날짜' in col or '일시' in col or 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df['year'] = df[col].dt.year
            df['month'] = df[col].dt.month
            df['day'] = df[col].dt.day
            df.drop(columns=[col], inplace=True)
            break

    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna(df[col].mode()[0])
        else:
            df[col] = df[col].fillna(df[col].mean())

    df.drop_duplicates(inplace=True)
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype("category").cat.codes

    model, scaler, feature_columns = load_weather_model()
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_columns]
    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)
    pred_mean = np.mean(y_pred, axis=0)
    np.save(os.path.join(SAVE_DIR, "latest_weather_pred.npy"), pred_mean)
    return pred_mean.tolist()


def predict_crop():
    weather_file = os.path.join(SAVE_DIR, "latest_weather_pred.npy")
    if not os.path.exists(weather_file):
        return None, "❌ 날씨 예측값 파일이 없습니다."

    weather_pred = np.load(weather_file)
    if len(weather_pred) < 3:
        return None, "❌ 날씨 예측값이 충분하지 않습니다."

    temp, hum, rain = weather_pred.tolist()
    model, scaler, le = load_crop_model()

    N, P, K, ph = 80, 50, 60, 6.5
    inp = np.array([[N, P, K, temp, hum, ph, rain]])
    inp_scaled = scaler.transform(inp)
    pred_proba = model.predict(inp_scaled)[0]

    top_indices = np.argsort(pred_proba)[::-1][:3]
    top_crops = le.inverse_transform(top_indices)
    top_probs = pred_proba[top_indices]

    crop_list = []
    for label, prob in zip(top_crops, top_probs):
        prob_val = round(float(prob), 4)
        if prob_val >= 0.8:
            grade = "높음"
        elif prob_val >= 0.5:
            grade = "보통"
        else:
            grade = "낮음"
        crop_list.append({
            "crop": label,
            "probability": prob_val,
            "grade": grade
        })

    return {
        "temperature": temp,
        "humidity": hum,
        "rainfall": rain,
        "recommendations": crop_list
    }, None


@app.route('/')
def home():
    return jsonify({
        "message": "작물 추천 API 서버입니다.",
        "endpoint": "/api/recommend_crop"
    })


@app.route('/api/recommend_crop')
def recommend_crop_api():
    try:
        weather = predict_weather()
        result, error = predict_crop()
        if error:
            return Response(json.dumps({"status": "error", "message": error}, ensure_ascii=False),
                            mimetype='application/json')

        response_data = {
            "status": "success",
            "weather": {
                "temperature": f"{weather[0]:.2f}°C",
                "humidity": f"{weather[1]:.2f}%",
                "rainfall": f"{weather[2]:.2f}mm"
            },
            "recommendations": result["recommendations"]
        }

        return Response(json.dumps(response_data, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        return Response(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False),
                        mimetype='application/json')
        
@app.route('/recommend_crop')
def render_crop_html():
    return render_template('crop_recommendation.html')

@app.route('/login')
def render_login_html():
    return render_template('login.html')

@app.route('/main')
def render_main_html():
    return render_template('main.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
