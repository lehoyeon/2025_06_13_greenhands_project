import os
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
import gradio as gr
import sys

# ========================
# 경로 설정
# ========================
SAVE_DIR = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep"
DATASET_DIR = os.path.join(SAVE_DIR, "dataset")

WEATHER_MODEL_PATH = os.path.join(SAVE_DIR, "weather_dl_model.h5")
WEATHER_SCALER_PATH = os.path.join(SAVE_DIR, "scaler_weather.pkl")
WEATHER_FEATURES_PATH = os.path.join(SAVE_DIR, "weather_features.pkl") # 예측 모델의 '입력 특성' 이름들이 저장된 파일
CROP_MODEL_PATH = os.path.join(SAVE_DIR, "crop_dnn_model.h5")
CROP_SCALER_PATH = os.path.join(SAVE_DIR, "scaler.pkl")
CROP_LE_PATH = os.path.join(SAVE_DIR, "label_encoder.pkl")

# 필요한 파일 존재 여부 확인 함수
def check_file_exists(filepath, name):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"필수 파일이 없습니다: {name} ({filepath})")

# ========================
# 모델 및 스케일러 로드 함수
# ========================
def load_weather_model():
    check_file_exists(WEATHER_MODEL_PATH, "날씨 예측 모델")
    check_file_exists(WEATHER_SCALER_PATH, "날씨 스케일러")
    check_file_exists(WEATHER_FEATURES_PATH, "날씨 특성 목록")
    
    model = load_model(WEATHER_MODEL_PATH)
    scaler = joblib.load(WEATHER_SCALER_PATH)
    feature_columns = joblib.load(WEATHER_FEATURES_PATH) # 이 리스트에는 모델의 입력 특성만 있어야 합니다.
    return model, scaler, feature_columns

def load_crop_model():
    check_file_exists(CROP_MODEL_PATH, "작물 추천 모델")
    check_file_exists(CROP_SCALER_PATH, "작물 스케일러")
    check_file_exists(CROP_LE_PATH, "작물 라벨 인코더")
    
    model = load_model(CROP_MODEL_PATH)
    scaler = joblib.load(CROP_SCALER_PATH)
    le = joblib.load(CROP_LE_PATH)
    return model, scaler, le

# ========================
# 날씨 예측 함수
# ========================
def predict_weather():
    check_file_exists(os.path.join(DATASET_DIR, "weather_2024.csv"), "날씨 데이터")
    df = pd.read_csv(os.path.join(DATASET_DIR, "weather_2024.csv"), encoding='cp949')

    # 날짜 컬럼 처리: 'year', 'month', 'day' 특성 생성
    date_col_name = None
    for col in df.columns:
        if '날짜' in col or '일시' in col or 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df['year'] = df[col].dt.year
            df['month'] = df[col].dt.month
            df['day'] = df[col].dt.day
            date_col_name = col
            break
    
    if date_col_name:
        df.drop(columns=[date_col_name], inplace=True)
    else:
        print("경고: 날짜 관련 컬럼을 찾을 수 없습니다. 'year', 'month', 'day' 특성이 생성되지 않았을 수 있습니다.")

    # 결측치 처리 (object 타입은 최빈값, 나머지는 평균)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna(df[col].mode()[0])
        else:
            df[col] = df[col].fillna(df[col].mean())

    df.drop_duplicates(inplace=True)

    # object 타입을 category code로 변환
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype("category").cat.codes

    # 모델, 스케일러, 특성 컬럼 로드
    model, scaler, feature_columns = load_weather_model()
    
    # === 디버깅을 위한 출력 ===
    print(f"\n--- Debugging `predict_weather` ---")
    print(f"df.columns (before selecting X): {df.columns.tolist()}")
    print(f"feature_columns (from weather_features.pkl): {feature_columns}")
    
    # feature_columns에 있지만 df에 없는 컬럼 확인 및 처리
    missing_in_df_for_X = [col for col in feature_columns if col not in df.columns]
    if missing_in_df_for_X:
        print(f"Warning: 'feature_columns'에 있지만 'df'에 없는 컬럼: {missing_in_df_for_X}. 0으로 채웁니다.")
        for col in missing_in_df_for_X:
            df[col] = 0 # 0으로 채우는 것이 적절한지 데이터에 따라 검토 필요

    # df에 있지만 feature_columns에 없는 컬럼 확인 (이것 자체는 에러 원인 아님)
    extra_in_df = [col for col in df.columns if col not in feature_columns]
    if extra_in_df:
        print(f"Info: 'df'에 있지만 'feature_columns'에 없는 컬럼: {extra_in_df}. 이 컬럼들은 예측에 사용되지 않습니다.")
    
    # feature_columns에 정의된 컬럼들만 정확한 순서로 선택하여 X를 구성합니다.
    X = df[feature_columns]
    print(f"X.columns (after selection for scaler.transform): {X.columns.tolist()}")
    print(f"--- End Debugging ---\n")

    # 스케일링
    X_scaled = scaler.transform(X)
    
    # 예측
    y_pred = model.predict(X_scaled)
    
    # 예측 결과는 날씨 지표 3가지(평균기온, 평균 상대습도, 일강수량)라고 가정
    pred_mean = np.mean(y_pred, axis=0) 

    np.save(os.path.join(SAVE_DIR, "latest_weather_pred.npy"), pred_mean)
    return pred_mean.tolist()

# ========================
# 작물 추천 함수
# ========================
def predict_crop():
    weather_file = os.path.join(SAVE_DIR, "latest_weather_pred.npy")
    if not os.path.exists(weather_file):
        return "❌ 날씨 예측값 파일이 없습니다. 먼저 날씨 예측을 실행해주세요.", ""

    weather_pred = np.load(weather_file)
    # weather_pred의 순서가 모델이 예측한 순서(예: 평균기온, 평균 상대습도, 일강수량)와 일치해야 합니다.
    if len(weather_pred) < 3:
        return "❌ 날씨 예측 결과가 예상보다 적습니다. (기온, 습도, 강수량 3가지 필요)", ""
        
    temp, hum, rain = weather_pred.tolist() 
    
    model, scaler, le = load_crop_model()
    
    # N, P, K, ph 값은 예시입니다. 실제 애플리케이션에서는 사용자 입력 등으로 받을 수 있습니다.
    N, P, K, ph = 80, 50, 60, 6.5
    
    # 작물 모델의 입력 특성 순서와 일치해야 합니다.
    # 이 부분은 crop_scaler.pkl이 fit될 때 사용된 특성 순서와 정확히 일치해야 합니다.
    inp = np.array([[N, P, K, temp, hum, ph, rain]]) 
    
    inp_scaled = scaler.transform(inp) 
    
    pred_proba = model.predict(inp_scaled)[0]
    pred_class_index = np.argmax(pred_proba)
    pred_label = le.inverse_transform([pred_class_index])[0]

    weather_text = f"**🗓️ 날씨 예측 결과:**\n🌡️ 온도: {temp:.2f}°C\n💧 습도: {hum:.2f}%\n🌧️ 강수량: {rain:.2f}mm"
    crop_text = f"**🌱 작물 추천 결과:**\n🌾 추천 작물: {pred_label}\n🔍 확률: {pred_proba[pred_class_index]:.2f}"
    return weather_text, crop_text

# ========================
# Gradio 인터페이스 정의
# ========================
def on_predict_button_clicked():
    try:
        predict_weather()
        return predict_crop()
    except Exception as e:
        # 에러 발생 시 사용자에게 친화적인 메시지 출력
        error_message = f"🚨 예측 실행 중 에러 발생: {str(e)}"
        print(error_message) # 콘솔에도 출력하여 디버깅 용이하게 함
        return error_message, error_message


with gr.Blocks() as demo:
    gr.Markdown("# 🌾 자동 날씨 예측 & 작물 추천 시스템")
    gr.Markdown("`weather_2024.csv` 파일의 데이터를 기반으로 미래 날씨를 예측하고, 이를 바탕으로 최적의 작물을 추천합니다.")
    
    with gr.Row():
        btn = gr.Button("예측 실행 및 작물 추천", variant="primary")
    
    with gr.Row():
        wout = gr.Textbox(label="날씨 예측 결과", lines=4, interactive=False)
        cout = gr.Textbox(label="작물 추천 결과", lines=4, interactive=False)
        
    btn.click(on_predict_button_clicked, inputs=[], outputs=[wout, cout])

# ========================
# 애플리케이션 실행
# ========================
if __name__ == "__main__":
    print(f"저장 디렉토리: {SAVE_DIR}")
    print(f"데이터셋 디렉토리: {DATASET_DIR}")
    
    # 모든 경로가 유효한지 시작 시점에 한 번 더 확인
    try:
        check_file_exists(WEATHER_MODEL_PATH, "weather_dl_model.h5")
        check_file_exists(WEATHER_SCALER_PATH, "scaler_weather.pkl")
        check_file_exists(WEATHER_FEATURES_PATH, "weather_features.pkl")
        check_file_exists(CROP_MODEL_PATH, "crop_dnn_model.h5")
        check_file_exists(CROP_SCALER_PATH, "scaler.pkl")
        check_file_exists(CROP_LE_PATH, "label_encoder.pkl")
        check_file_exists(os.path.join(DATASET_DIR, "weather_2024.csv"), "weather_2024.csv")
        print("모든 필요한 파일이 존재합니다. 애플리케이션을 시작합니다.")
        demo.launch(share=True)
    except FileNotFoundError as e:
        print(f"애플리케이션 시작 실패: {e}")
        print("필요한 모델 파일, 스케일러 파일, 특성 파일 또는 데이터셋 파일이 올바른 경로에 있는지 확인해주세요.")
        print(f"현재 설정된 SAVE_DIR: {SAVE_DIR}")
        print(f"현재 설정된 DATASET_DIR: {DATASET_DIR}")
    except Exception as e:
        print(f"예기치 않은 에러로 애플리케이션 시작 실패: {e}")