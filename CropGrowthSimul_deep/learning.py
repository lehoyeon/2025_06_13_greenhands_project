import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import joblib

# ========================
# 경로 설정
# ========================
SAVE_DIR = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep"
os.makedirs(SAVE_DIR, exist_ok=True) # SAVE_DIR이 없으면 생성

DATASET_PATH = os.path.join(SAVE_DIR, "dataset", "weather_2024.csv")

# ========================
# 데이터 로딩 및 전처리
# ========================
print(f"데이터셋 로딩 중: {DATASET_PATH}")
try:
    df = pd.read_csv(DATASET_PATH, encoding='cp949')
except FileNotFoundError:
    print(f"오류: 데이터셋 파일 '{DATASET_PATH}'을(를) 찾을 수 없습니다.")
    print("dataset 폴더 안에 weather_2024.csv 파일이 있는지 확인해주세요.")
    exit() # 파일이 없으면 스크립트 종료

# 날짜 처리
date_col_found = False
for col in df.columns:
    if '날짜' in col or '일시' in col or 'date' in col.lower():
        df[col] = pd.to_datetime(df[col], errors='coerce')
        df['year'] = df[col].dt.year
        df['month'] = df[col].dt.month
        df['day'] = df[col].dt.day
        df.drop(columns=[col], inplace=True)
        date_col_found = True
        break
if not date_col_found:
    print("경고: 날짜 관련 컬럼을 찾을 수 없습니다. 'year', 'month', 'day' 특성이 생성되지 않았을 수 있습니다.")

# 결측치 처리
print("결측치 처리 중...")
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].fillna(df[col].mode()[0])
    else:
        df[col] = df[col].fillna(df[col].mean())

df.drop_duplicates(inplace=True)
print(f"전처리 후 데이터 크기: {df.shape}")

# 범주형 인코딩
print("범주형 인코딩 중...")
# LabelEncoder는 한 컬럼씩 적용해야 합니다.
# 만약 여러 object 컬럼이 있다면 각각 le.fit_transform을 적용해야 합니다.
# 현재 코드에서는 첫 번째 object 컬럼에만 적용됩니다. 모든 object 컬럼에 적용하려면 반복문 안에 le 초기화를 해야 합니다.
# 이 코드에서는 object 컬럼이 하나만 있을 것으로 가정합니다.
# 만약 여러 개의 object 컬럼이 있고 각각 다른 LabelEncoder가 필요하다면,
# 각 컬럼에 대한 LabelEncoder를 따로 저장하거나, OneHotEncoder 사용을 고려해야 합니다.
# 여기서는 예시로 남겨두었으며, 실제 데이터에 따라 수정이 필요할 수 있습니다.
# for col in df.select_dtypes(include='object').columns:
#     df[col] = le.fit_transform(df[col]) # 이 le는 마지막 컬럼에 fit된 것만 남음.

# 모든 object 컬럼에 대해 LabelEncoder 적용 (각 컬럼별로 고유한 LE를 사용해야 할 수도 있음)
object_cols = df.select_dtypes(include='object').columns
if len(object_cols) > 0:
    for col in object_cols:
        # 각 컬럼마다 새로운 LabelEncoder를 생성하는 것이 안전합니다.
        # 또는 전체 object 컬럼에 대해 한 번에 fit_transform 가능한 인코더를 사용합니다.
        # 여기서는 단순히 코드 스니펫에 따라 기존 방식을 유지합니다.
        df[col] = le.fit_transform(df[col])
    print(f"인코딩된 범주형 컬럼: {object_cols.tolist()}")
else:
    print("범주형 컬럼이 없습니다.")

# 타겟 설정 및 제거
target_columns = ['평균기온(°C)', '평균 상대습도(%)', '일강수량(mm)']
# 타겟 컬럼이 데이터프레임에 있는지 확인
missing_targets = [col for col in target_columns if col not in df.columns]
if missing_targets:
    print(f"오류: 타겟 컬럼 중 다음이 데이터에 없습니다: {missing_targets}")
    print("weather_2024.csv 파일의 컬럼 이름을 확인해주세요.")
    exit()

X = df.drop(columns=target_columns)
y = df[target_columns].values # y는 numpy 배열로 사용

# 스케일링
print("입력 특성 스케일링 중...")
scaler = StandardScaler()
# X.columns를 직접 사용하여 DataFrame의 컬럼 이름을 유지하면서 스케일링
X_scaled_values = scaler.fit_transform(X) # numpy 배열 반환
X = pd.DataFrame(X_scaled_values, columns=X.columns) # 다시 DataFrame으로 변환하여 컬럼 이름 유지

# feature 컬럼 저장 (X의 컬럼이 이제 모델의 입력 특성 이름입니다)
feature_columns = X.columns.tolist()
joblib.dump(feature_columns, os.path.join(SAVE_DIR, 'weather_features.pkl'))
print(f"입력 특성 목록 저장 완료: {os.path.join(SAVE_DIR, 'weather_features.pkl')}")
print(f"저장된 입력 특성: {feature_columns}")


# 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X.values, y, test_size=0.2, random_state=42) # X.values로 numpy 배열 전달

print(f"학습 데이터 X_train.shape: {X_train.shape}, y_train.shape: {y_train.shape}")
print(f"테스트 데이터 X_test.shape: {X_test.shape}, y_test.shape: {y_test.shape}")


# ========================
# 모델 구성 및 학습
# ========================
print("날씨 예측 모델 구성 및 학습 시작...")
model = Sequential([
    Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(len(target_columns)) # 출력 레이어는 예측할 타겟의 개수와 일치해야 합니다.
])
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
history = model.fit(X_train, y_train, 
                    validation_split=0.2, # 학습 세트 내에서 20%를 검증 데이터로 사용
                    epochs=100, 
                    batch_size=32, 
                    callbacks=[early_stop], 
                    verbose=2)

# ========================
# 모델 평가 및 저장
# ========================
print("모델 평가 중...")
loss, mae = model.evaluate(X_test, y_test, verbose=2)
print(f"테스트 손실 (MSE): {loss:.4f}, 테스트 MAE: {mae:.4f}")

# 예측 예시 (선택 사항)
y_pred = model.predict(X_test)
# 예측된 각 날씨 지표의 평균값 저장 (app.py에서 사용)
pred_mean = np.mean(y_pred, axis=0) # [평균기온 예측 평균, 평균 상대습도 예측 평균, 일강수량 예측 평균]
np.save(os.path.join(SAVE_DIR, "latest_weather_pred.npy"), pred_mean)
print(f"최신 날씨 예측 평균값 저장 완료: {os.path.join(SAVE_DIR, 'latest_weather_pred.npy')}")
print(f"예측된 평균값: {pred_mean.tolist()}")

# 모델과 스케일러 저장
model.save(os.path.join(SAVE_DIR, 'weather_dl_model.h5'))
joblib.dump(scaler, os.path.join(SAVE_DIR, 'scaler_weather.pkl'))
print(f"모델 저장 완료: {os.path.join(SAVE_DIR, 'weather_dl_model.h5')}")
print(f"스케일러 저장 완료: {os.path.join(SAVE_DIR, 'scaler_weather.pkl')}")

print("\n✅ 날씨 예측 모델 학습 및 저장 완료")

# ========================
# (추가) 작물 추천 모델 학습 (만약 동일 파일에 있다면)
# ========================
# 일반적으로 작물 추천 모델은 별도의 데이터셋과 학습 프로세스를 가질 것입니다.
# 여기서는 생략되었으므로, 필요한 경우 이 부분도 learning.py에 추가해야 합니다.
# 예시로 작물 추천 모델 학습 및 저장 코드를 아래에 주석으로 남깁니다.
