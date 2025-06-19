import pandas as pd
import os

# 데이터 파일 경로
DATASET_DIR = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep\dataset"
csv_file = os.path.join(DATASET_DIR, "weather_2024.csv")

# 1. 데이터 로드 및 기본 정보 확인
print("=== 데이터 기본 정보 ===")
try:
    df = pd.read_csv(csv_file, encoding='cp949')
    print(f"데이터 형태: {df.shape}")
    print(f"컬럼 목록: {df.columns.tolist()}")
    print("\n=== 각 컬럼의 데이터 타입 ===")
    print(df.dtypes)
    
    print("\n=== 데이터 미리보기 (상위 5행) ===")
    print(df.head())
    
    # 2. 타겟 컬럼 존재 여부 확인
    target_columns = ['평균기온(°C)', '평균 상대습도(%)', '일강수량(mm)']
    print(f"\n=== 타겟 컬럼 존재 여부 ===")
    for col in target_columns:
        exists = col in df.columns
        print(f"{col}: {'✅ 존재' if exists else '❌ 없음'}")
    
    # 3. 유사한 컬럼명 찾기
    print(f"\n=== 기온 관련 컬럼 ===")
    temp_cols = [col for col in df.columns if '기온' in col or '온도' in col or 'temp' in col.lower()]
    print(temp_cols)
    
    print(f"\n=== 습도 관련 컬럼 ===")
    hum_cols = [col for col in df.columns if '습도' in col or 'hum' in col.lower()]
    print(hum_cols)
    
    print(f"\n=== 강수 관련 컬럼 ===")
    rain_cols = [col for col in df.columns if '강수' in col or '비' in col or 'rain' in col.lower() or 'precipitation' in col.lower()]
    print(rain_cols)
    
    # 4. 날짜 관련 컬럼 확인
    print(f"\n=== 날짜 관련 컬럼 ===")
    date_cols = [col for col in df.columns if '날짜' in col or '일시' in col or 'date' in col.lower()]
    print(date_cols)
    
    # 5. 결측치 확인
    print(f"\n=== 결측치 정보 ===")
    missing_info = df.isnull().sum()
    missing_cols = missing_info[missing_info > 0]
    if len(missing_cols) > 0:
        print("결측치가 있는 컬럼:")
        print(missing_cols)
    else:
        print("결측치 없음")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print("파일 경로나 인코딩을 확인하세요.")