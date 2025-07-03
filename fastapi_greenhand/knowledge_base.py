# knowledge_base.py (find_recommended_crops는 이제 ai_service에서 직접 사용하지 않지만, 그대로 유지해도 됨)
import json
from typing import List, Dict, Any, Union, Optional 

# ★★★ CROPS_DATA는 이제 AI 모델에게 요청할 JSON 형식의 예시 및 가이드에 사용될 뿐,
# 직접적인 추천 데이터 소스로 사용되지 않습니다. 하지만 get_crop_by_id는 여전히 사용됩니다. ★★★
CROPS_DATA = [
    {
        "id": "lettuce",
        "name": "상추",
        "cultivation_duration": "short", 
        "cultivation_location": ["indoor", "outdoor"],
        "suitable_regions": ["seoul", "gyeonggi", "chungbuk", "all"],
        "thumbnail_image": "/images/lettuce_thumbnail.png",
        "initial_preparations": ["씨앗 또는 모종", "지름 10cm 이상 화분", "배수가 잘 되는 상토", "물뿌리개"],
        "difficulty": "하",
        "pot_size": "10cm 이상",
        "water_amount": "매일 (흙 마르지 않게)",
        "soil_type": "배수 좋은 토양",
        "pest_control": "진딧물 발생 시 친환경 살충제",
        "detailed_guide": { 
            "step1": "씨앗 심기: 씨앗을 흙에 0.5cm 깊이로 심고 흙으로 덮어줍니다.",
            "step2": "물 주기: 흙이 마르지 않게 매일 충분히 물을 줍니다. 과습은 피해주세요.",
            "step3": "햇빛: 하루 4~6시간 이상 햇빛을 볼 수 있는 곳에 둡니다 (반그늘도 가능).",
            "step4": "수확: 잎이 10cm 정도 자라면 바깥 잎부터 수확합니다."
        }
    },
    {
        "id": "radish",
        "name": "무",
        "cultivation_duration": "medium",
        "cultivation_location": ["outdoor"],
        "suitable_regions": ["gangwon", "chungnam", "gyeongbuk", "all"],
        "thumbnail_image": "/images/radish_thumbnail.png",
        "initial_preparations": ["무 씨앗", "깊이 20cm 이상 텃밭 또는 큰 화분", "비옥하고 부드러운 흙"],
        "difficulty": "중",
        "pot_size": "20cm 이상",
        "water_amount": "주 2~3회 (흙 마르면)",
        "soil_type": "부드럽고 비옥한 토양",
        "pest_control": "배추흰나비 애벌레 주의",
        "detailed_guide": [ 
            "1. 파종: 씨앗을 2~3cm 간격으로 심고 얇게 흙을 덮습니다.",
            "2. 물 주기: 흙이 촉촉하도록 유지하되 과습은 피합니다.",
            "3. 솎아주기: 본잎이 2~3장 나오면 간격을 넓혀줍니다.",
            "4. 수확: 파종 후 2~3개월 뒤 뿌리가 충분히 자라면 수확합니다."
        ]
    },
    {
        "id": "tomato",
        "name": "방울토마토",
        "cultivation_duration": "long",
        "cultivation_location": ["outdoor", "indoor"],
        "suitable_regions": ["seoul", "gyeonggi", "jeju", "all"],
        "thumbnail_image": "/images/tomato_thumbnail.png",
        "initial_preparations": ["모종", "큰 화분/텃밭", "지지대", "퇴비"],
        "difficulty": "중",
        "pot_size": "25cm 이상",
        "water_amount": "매일 (열매 맺을 시기)",
        "soil_type": "영양분 풍부한 토양",
        "pest_control": "진딧물, 응애, 잿빛곰팡이병",
        "detailed_guide": [
            "1. 모종 심기: 햇빛이 잘 드는 곳에 모종을 심고 지지대를 세웁니다.",
            "2. 물 주기: 흙이 마르지 않게 꾸준히 물을 줍니다.",
            "3. 순지르기: 겨드랑이 순을 제거하여 영양분 분산을 막습니다.",
            "4. 수확: 열매가 빨갛게 익으면 수확합니다."
        ]
    },
    {
        "id": "basil",
        "name": "바질",
        "cultivation_duration": "short",
        "cultivation_location": ["indoor", "outdoor"],
        "suitable_regions": ["seoul", "all"],
        "thumbnail_image": "/images/basil_thumbnail.png",
        "initial_preparations": ["씨앗", "작은 화분", "배수 좋은 흙"],
        "difficulty": "하",
        "pot_size": "10cm 이상",
        "water_amount": "2~3일에 한 번",
        "soil_type": "약간 습한 토양",
        "pest_control": "응애, 잎마름병",
        "detailed_guide": [
            "1. 파종: 씨앗을 흙에 흩뿌리고 얇게 흙을 덮습니다.",
            "2. 물 주기: 흙이 마르면 바로 물을 줍니다.",
            "3. 햇빛: 햇빛이 잘 드는 곳에 둡니다 (반그늘도 가능).",
            "4. 수확: 잎이 어느 정도 자라면 필요한 만큼 따서 사용합니다."
        ]
    },
    {
        "id": "potato",
        "name": "감자",
        "cultivation_duration": "medium",
        "cultivation_location": ["outdoor"],
        "suitable_regions": ["gangwon", "jeonbuk", "all"],
        "thumbnail_image": "/images/potato_thumbnail.png",
        "initial_preparations": ["씨감자", "텃밭/큰 화분", "거름"],
        "difficulty": "중",
        "pot_size": "깊이 30cm 이상",
        "water_amount": "주 1~2회",
        "soil_type": "배수 좋은 사질토",
        "pest_control": "감자역병, 잎말이병",
        "detailed_guide": [
            "1. 씨감자 준비: 싹이 난 씨감자를 준비합니다.",
            "2. 심기: 싹이 위로 오도록 흙에 심습니다.",
            "3. 흙 덮어주기: 줄기가 자라면 흙으로 덮어줍니다.",
            "4. 수확: 잎이 시들기 시작하면 수확합니다."
        ]
    }
]

# ★★★ 이 함수는 이제 ai_service.py에서 직접 사용되지 않습니다.
# 하지만 다른 곳에서 사용될 수 있으므로 일단 유지합니다. ★★★
def get_all_crops() -> List[Dict[str, Any]]:
    """모든 작물 데이터를 반환합니다."""
    return CROPS_DATA

def get_crop_by_id(crop_id: str) -> Optional[Dict[str, Any]]:
    """주어진 ID에 해당하는 작물 데이터를 반환합니다."""
    for crop in CROPS_DATA:
        if crop['id'] == crop_id:
            return crop
    return None

def find_recommended_crops(duration: str, environment: str, region: str, limit: int = 5) -> List[Dict[str, Any]]:
    """주어진 조건에 맞는 작물을 추천합니다. (이제 ai_service에서는 사용되지 않음)"""
    recommended = []
    for crop in CROPS_DATA:
        env_match = environment in crop['cultivation_location']
        duration_match = crop['cultivation_duration'] == duration
        region_match = (region == 'all') or \
                    (region in crop['suitable_regions']) or \
                    ('all' in crop['suitable_regions'])

        if env_match and duration_match and region_match:
            recommended.append(crop)
            if len(recommended) >= limit:
                break
    return recommended

# --- 기존 지식 데이터베이스 (챗봇용) ---
# 이 부분은 챗봇의 일반적인 응답에 사용되므로 그대로 유지합니다.
agricultural_knowledge_base = {
    "상추 재배 방법": {
        "summary": "상추는 서늘하고 햇볕이 잘 드는 곳에서 잘 자라며, 꾸준한 물 관리가 중요합니다.",
        "details": "상추는 직사광선보다는 반그늘을 선호하며, 특히 여름철에는 고온에 약하므로 서늘한 환경을 유지해주는 것이 좋습니다. 씨앗을 심은 후 싹이 나면 건강한 모종만 남기고 솎아주세요. 흙이 마르지 않도록 주기적으로 물을 주되, 과습은 피해야 합니다. 보통 파종 후 30~40일이면 수확할 수 있습니다."
    },
    "토마토 병충해": {
        "summary": "토마토에는 탄저병, 역병, 온실가루이 등 다양한 병충해가 발생할 수 있습니다.",
        "details": "토마토에 흔히 발생하는 병충해로는 잎에 검은 반점이 생기는 탄저병, 식물 전체가 시들게 되는 역병, 그리고 잎 뒷면에 흰색 벌레가 생기는 온실가루이 등이 있습니다. 각 병충해는 증상이 다르므로 정확한 진단 후 적절한 유기농 방제제나 친환경 농법으로 관리하는 것이 중요합니다. 예방을 위해 통풍을 잘 시키고, 적절한 영양 관리를 해주세요."
    },
    "딸기 수확 시기": {
        "summary": "딸기는 품종과 재배 환경에 따라 다르지만, 일반적으로 4월에서 6월 사이에 주로 수확합니다.",
        "details": "노지 딸기는 보통 4월 말에서 6월 초에 수확이 시작되며, 시설 재배의 경우 겨울철에도 수확이 가능합니다. 딸기 열매 전체가 붉게 익었을 때가 수확 적기이며, 너무 오래 두면 무르거나 병에 걸리기 쉬우니 주의해야 합니다. 수확은 보통 아침 일찍 하는 것이 신선도 유지에 유리합니다."
    },
    "스마트팜이란?": {
        "summary": "스마트팜은 정보통신기술(ICT)을 활용하여 작물 재배 환경을 자동 및 원격으로 관리하는 지능형 농장입니다.",
        "details": "스마트팜은 센서를 통해 온도, 습도, 이산화탄소 농도, 토양 수분 등 작물 생육에 필요한 환경 정보를 실시간으로 수집하고, 이를 바탕으로 관수, 비료 공급, 환기 등을 자동으로 제어합니다. 스마트폰이나 컴퓨터로 언제 어디서든 농장을 관리할 수 있어 생산 효율성을 높이고 노동력을 절감하는 데 기여합니다."
    },
    "온도 조절 중요성": {
        "summary": "작물 생육에서 온도는 매우 중요한 요소로, 적정 온도를 유지하는 것이 건강한 성장에 필수적입니다.",
        "details": "각 작물은 생육 단계별로 최적의 온도가 다릅니다. 온도가 너무 높거나 낮으면 작물이 스트레스를 받아 성장이 저해되거나, 심하면 고사할 수도 있습니다. 예를 들어, 야간 온도가 너무 높으면 식물이 호흡량이 늘어 양분 소모가 많아지고, 과도하게 낮으면 냉해를 입을 수 있습니다. 정밀한 온도 관리는 작물의 품질과 수확량을 결정하는 중요한 요인입니다."
    },
    "질병 진단 기능": {
        "summary": "식물 잎사귀 이미지를 업로드하시면 AI가 질병 또는 해충을 진단하고 해결책을 안내해 드립니다.",
        "details": "초록손 앱의 질병 진단 기능을 통해 식물 잎, 줄기, 열매 등의 이상 증상 사진을 업로드해 보세요. 인공지능이 분석하여 예상되는 질병이나 해충의 종류, 심각도, 그리고 초기 방제 및 관리 방법을 알려드립니다. [질병 진단 바로가기](/PRH-002) 버튼을 눌러 바로 이용하실 수 있습니다.",
        "link": "/PRH-002"
    },
    "시뮬레이션 기능": {
        "summary": "농작물 시뮬레이션 기능으로 재배 환경에 따른 미래 생육 상태를 예측하고 시각화할 수 있습니다.",
        "details": "초록손 시뮬레이션 기능은 재배할 농작물 종류를 선택하고 온도, 습도, 일조량 등 환경 조건을 입력하면, 해당 조건에서 예상되는 작물의 성장 곡선, 예상 수확량 등을 예측하여 시각적으로 보여줍니다. 이를 통해 최적의 재배 조건을 찾아 성공적인 농사를 계획하는 데 도움을 받을 수 있습니다. [농작물 시뮬레이션 바로가기](/PRH-003) 버튼을 클릭해 지금 바로 시작해 보세요!",
        "link": "/PRH-003"
    },
    "내 농장 확인": {
        "summary": "내 농장 기능을 통해 현재 키우시는 작물의 성장 진행도를 한눈에 확인하고 효율적으로 관리하세요.",
        "details": "초록손의 '내 농장' 페이지에서는 등록된 작물들의 현재 생육 상태, 물 주기 알림, 병충해 발생 이력 등을 종합적으로 관리할 수 있습니다. 각 작물의 성장 일지를 기록하고, 필요할 때 맞춤형 가이드를 받아보세요. [내 농장 바로가기](/my_farm_page_id) 버튼을 눌러 이동하실 수 있습니다.",
        "link": "/my_farm_page_id"
    },
    "엑셀 보고서": {
        "summary": "요청하신 엑셀 보고서 파일을 생성해 드립니다.",
        "details": "엑셀 보고서는 주로 표 형식의 데이터를 정리하고 분석하는 데 유용합니다. 제가 알려드린 정보 중 표로 정리될 수 있는 데이터가 있다면 엑셀 파일로 제공해 드릴 수 있습니다. '엑셀 보고서 생성해 줘'와 같이 명확하게 요청해 주시면 해당 기능을 호출합니다."
    },
    "워드 보고서": {
        "summary": "요청하신 워드 보고서 파일을 생성해 드립니다.",
        "details": "워드 보고서는 텍스트 기반의 상세한 정보나 설명이 필요할 때 적합합니다. 제가 제공해 드린 농업 정보, 진단 결과 등의 내용을 문서 형태로 정리하여 워드 파일로 만들어 드릴 수 있습니다. '워드 보고서 만들어 줘'와 같이 말씀해 주시면 보고서 생성을 도와드리겠습니다."
    }
}