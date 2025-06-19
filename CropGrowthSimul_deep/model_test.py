import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping
import joblib

# 작업 경로, 저장 경로 지정
DATA_PATH = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep\dataset\Crop_recommendation.csv"
SAVE_DIR = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep"

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 데이터 로드
df = pd.read_csv(DATA_PATH)

# 결측치 처리
df = df.dropna()

# 피처/레이블 분리
feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
X = df[feature_cols].values
y = df['label'].values

# 레이블 인코딩
le = LabelEncoder()
y_encoded = le.fit_transform(y)
y_categorical = to_categorical(y_encoded)

# 스케일링
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 모델 설계 (간단한 DNN)
model = Sequential([
    Dense(64, activation='relu', input_shape=(X_scaled.shape[1],)),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(y_categorical.shape[1], activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 조기 종료 콜백
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# 학습
model.fit(X_scaled, y_categorical, epochs=100, batch_size=32, validation_split=0.2, callbacks=[early_stop])

# 저장
model.save(os.path.join(SAVE_DIR, 'crop_dnn_model.h5'))
joblib.dump(scaler, os.path.join(SAVE_DIR, 'scaler.pkl'))
joblib.dump(le, os.path.join(SAVE_DIR, 'label_encoder.pkl'))

print("모델, 스케일러, 레이블 인코더가 저장되었습니다.")
