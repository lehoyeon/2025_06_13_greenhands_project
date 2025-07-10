# knowledge_base.py

import json
from typing import List, Dict, Any, Union, Optional

# --- ⭐⭐ CROPS_DATA: 물 주는 주기 상세 정보 및 단계별 가이드 포함 ⭐⭐ ---
CROPS_DATA = [
    # ... (기존 CROPS_DATA 내용은 유지) ...
    {
        "id": "lettuce",
        "name": "상추",
        "cultivation_duration": "short",
        "cultivation_location": ["indoor", "outdoor"],
        "suitable_regions": ["서울", "경기", "충북", "모든 지역"],
        "thumbnail_image": "/img/lettuce.jpg",
        "initial_preparations": ["씨앗 또는 모종", "지름 10cm 이상 화분", "배수가 잘 되는 상토", "물뿌리개"],
        "difficulty": "하",
        "pot_size": "10cm 이상",
        "water_amount": "매일 (흙 마르지 않게)",
        "watering_frequency_detail": {
            "interval_text": "매일",
            "condition_text": "흙 마름 확인 후",
            "typical_interval_days": 1,
            "amount_ml": 200,
            "watering_time_suggestions": ["오전", "오후"],
            "min_interval_hours": 8
        },
        "soil_type": "배수 좋은 토양",
        "pest_control": "진딧물 발생 시 친환경 살충제",
        "detailed_guides_by_stage": {
            "파종": {
                "title": "상추 파종 가이드",
                "guide_text": [
                    "씨앗을 흙에 0.5cm 깊이로 심고 흙으로 덮어줍니다.",
                    "발아 온도는 15~20°C가 적정합니다.",
                    "햇빛이 잘 드는 곳에 두고 흙이 마르지 않도록 촉촉하게 유지합니다."
                ],
                "image_tip": "/img/lettuce_stage_sowing.png"
            },
            "새싹": {
                "title": "상추 새싹 관리",
                "guide_text": [
                    "새싹이 나오면 햇빛을 충분히 받을 수 있는 곳에 둡니다 (하루 4~6시간).",
                    "흙이 마르지 않게 매일 물을 줍니다. 과습은 피해주세요.",
                    "튼튼한 새싹만 남기고 2~3cm 간격으로 솎아줍니다."
                ],
                "image_tip": "/img/lettuce_stage_sprout.png"
            },
            "성장": {
                "title": "상추 성장기 관리",
                "guide_text": [
                    "잎이 5~10cm 정도 자라면 액비(액체 비료)를 묽게 타서 줍니다 (선택 사항).",
                    "통풍이 잘 되도록 관리하여 곰팡이나 진딧물을 예방합니다.",
                    "너무 덥거나 건조하면 잎 끝이 탈 수 있으니 주의합니다."
                ],
                "image_tip": "/img/lettuce_stage_growth.png"
            },
            "수확": {
                "title": "상추 수확 가이드",
                "guide_text": [
                    "잎이 충분히 자라면 바깥 잎부터 필요한 만큼 수확합니다.",
                    "안쪽 잎은 계속 자라므로 반복 수확이 가능합니다.",
                    "한 번에 너무 많은 잎을 따면 식물이 약해질 수 있습니다."
                ],
                "image_tip": "/img/lettuce_stage_harvest.png"
            },
            "기타": {
                "title": "상추 일반 관리 팁",
                "guide_text": [
                    "상추는 서늘한 기후를 좋아합니다 (15~20°C).",
                    "햇빛이 부족하면 웃자라니 주의하세요."
                ]
            }
        },
        "detailed_guide": {},
        "expected_cultivation_days": 30
    },
    {
        "id": "radish",
        "name": "무",
        "cultivation_duration": "medium",
        "cultivation_location": ["outdoor"],
        "suitable_regions": ["강원", "충남", "경북", "모든 지역"],
        "thumbnail_image": "/img/radish.jpg",
        "initial_preparations": ["무 씨앗", "깊이 20cm 이상 텃밭 또는 큰 화분", "비옥하고 부드러운 흙"],
        "difficulty": "중",
        "pot_size": "20cm 이상",
        "water_amount": "주 2~3회 (흙 마르면)",
        "watering_frequency_detail": {
            "interval_text": "주 2~3회",
            "condition_text": "흙 마름 확인 후",
            "typical_interval_days": 3,
            "amount_ml": 300,
            "watering_time_suggestions": ["오전"],
            "min_interval_hours": 24
        },
        "soil_type": "부드럽고 비옥한 토양",
        "pest_control": "배추흰나비 애벌레 주의",
        "detailed_guides_by_stage": {
            "파종": {
                "title": "무 파종 가이드",
                "guide_text": [
                    "씨앗을 2~3cm 간격으로 심고 얇게 흙을 덮습니다.",
                    "발아를 위해 흙을 촉촉하게 유지합니다."
                ]
            },
            "성장": {
                "title": "무 성장기 관리",
                "guide_text": [
                    "본잎이 2~3장 나오면 간격을 넓혀줍니다 (솎아내기).",
                    "뿌리 비대를 위해 비옥한 토양을 유지하고 충분히 물을 줍니다."
                ]
            },
            "수확": {
                "title": "무 수확 가이드",
                "guide_text": [
                    "파종 후 2~3개월 뒤 뿌리가 충분히 자라면 수확합니다.",
                    "무청을 잡고 살살 흔들어 뽑아냅니다."
                ]
            }
        },
        "detailed_guide": [],
        "expected_cultivation_days": 60
    },
    {
        "id": "tomato",
        "name": "방울토마토",
        "cultivation_duration": "long",
        "cultivation_location": ["outdoor", "indoor"],
        "suitable_regions": ["서울", "경기", "제주", "모든 지역"],
        "thumbnail_image": "/img/cherry_tomato.jpg",
        "initial_preparations": ["모종", "큰 화분/텃밭", "지지대", "퇴비"],
        "difficulty": "중",
        "pot_size": "25cm 이상",
        "water_amount": "매일 (열매 맺을 시기)",
        "watering_frequency_detail": {
            "interval_text": "매일 (열매 맺을 시기)",
            "condition_text": "흙 마름 확인 후",
            "typical_interval_days": 1,
            "amount_ml": 500,
            "watering_time_suggestions": ["오전"],
            "min_interval_hours": 24
        },
        "soil_type": "영양분 풍부한 토양",
        "pest_control": "진딧물, 응애, 잿빛곰팡이병",
        "detailed_guides_by_stage": {
            "파종": {
                "title": "방울토마토 씨앗 심기",
                "guide_text": [
                    "씨앗을 흙에 1cm 정도 깊이로 심고 물을 충분히 줍니다.",
                    "발아 온도는 25~30°C가 적정합니다."
                ]
            },
            "새싹": {
                "title": "방울토마토 새싹 관리",
                "guide_text": [
                    "새싹이 나오면 햇빛이 잘 드는 곳에 둡니다.",
                    "본잎이 2~3장 나오면 튼튼한 개체만 남기고 솎아줍니다."
                ]
            },
            "성장": {
                "title": "방울토마토 성장 관리",
                "guide_text": [
                    "줄기가 굵어지기 시작하면 지지대를 세워줍니다.",
                    "성장 초기에 질소 비료를, 꽃이 필 때 인산 비료를 줍니다."
                ]
            },
            "개화": {
                "title": "방울토마토 개화 관리",
                "guide_text": [
                    "꽃이 피면 흔들어주거나 붓으로 인공수분을 해주면 결실률을 높일 수 있습니다.",
                    "꽃이 많이 피는 시기에는 물 관리에 특히 신경 씁니다."
                ]
            },
            "결실": {
                "title": "방울토마토 결실 관리",
                "guide_text": [
                    "열매가 맺히기 시작하면 영양 공급을 꾸준히 해줍니다.",
                    "물 관리가 중요하며, 너무 건조하면 열과가 발생할 수 있습니다."
                ]
            },
            "수확": {
                "title": "방울토마토 수확",
                "guide_text": [
                    "열매 전체가 빨갛게 익으면 수확합니다. 완숙되기 전에 따면 맛이 덜할 수 있습니다.",
                    "수확 시기에는 물을 줄여 당도를 높일 수 있습니다."
                ]
            }
        },
        "detailed_guide": [],
        "expected_cultivation_days": 90
    },
    {
        "id": "basil",
        "name": "바질",
        "cultivation_duration": "short",
        "cultivation_location": ["indoor", "outdoor"],
        "suitable_regions": ["서울", "모든 지역"],
        "thumbnail_image": "/img/Basil.jpg",
        "initial_preparations": ["씨앗 또는 모종", "작은 화분", "배수 좋은 흙"],
        "difficulty": "하",
        "pot_size": "10cm 이상",
        "water_amount": "흙 마르면 바로",
        "watering_frequency_detail": {
            "interval_text": "흙 마르면 바로",
            "condition_text": "흙 마름 확인 후",
            "typical_interval_days": 1.5,
            "amount_ml": 150,
            "watering_time_suggestions": ["오전"],
            "min_interval_hours": 24
        },
        "soil_type": "약간 습한 토양",
        "pest_control": "응애, 잎마름병",
        "detailed_guides_by_stage": {
            "파종": {
                "title": "바질 씨앗 심기",
                "guide_text": [
                    "씨앗을 흙에 얕게 흩뿌리고 얇게 흙을 덮습니다.",
                    "발아 온도는 20~25°C가 적정합니다."
                ]
            },
            "새싹": {
                "title": "바질 새싹 관리",
                "guide_text": [
                    "모종을 심은 후 바로 물을 줍니다.",
                    "새싹이 돋아나면 햇빛이 잘 드는 곳으로 옮깁니다 (하루 6시간 이상)."
                ]
            },
            "성장": {
                "title": "바질 성장 관리",
                "guide_text": [
                    "줄기가 자라면 순지르기를 하여 옆가지 성장을 유도하고 풍성하게 키웁니다.",
                    "정기적으로 물을 주고 통풍을 신경 씁니다. 과습을 피하세요."
                ]
            },
            "수확": {
                "title": "바질 수확",
                "guide_text": [
                    "잎이 충분히 자라면 순지르기하듯이 잎을 따서 수확합니다.",
                    "꽃대가 올라오면 바로 잘라주어 잎의 향을 유지합니다."
                ]
            }
        },
        "detailed_guide": [],
        "expected_cultivation_days": 45
    },
    {
        "id": "potato",
        "name": "감자",
        "cultivation_duration": "medium",
        "cultivation_location": ["outdoor"],
        "suitable_regions": ["강원", "전북", "모든 지역"],
        "thumbnail_image": "/img/potato.jpg",
        "initial_preparations": ["씨감자", "텃밭/큰 화분", "거름"],
        "difficulty": "중",
        "pot_size": "깊이 30cm 이상",
        "water_amount": "주 1~2회",
        "watering_frequency_detail": {
            "interval_text": "주 1~2회",
            "condition_text": "흙 마름 확인 후",
            "typical_interval_days": 5,
            "amount_ml": 800,
            "watering_time_suggestions": ["오전"],
            "min_interval_hours": 24
        },
        "soil_type": "배수 좋은 사질토",
        "pest_control": "감자역병, 잎말이병",
        "detailed_guides_by_stage": {
            "파종": {
                "title": "감자 씨감자 심기",
                "guide_text": [
                    "싹이 난 씨감자를 준비합니다. 큰 감자는 싹이 2~3개씩 붙도록 잘라서 심습니다.",
                    "흙에 10~15cm 깊이로 심고 흙을 덮어줍니다."
                ]
            },
            "성장": {
                "title": "감자 성장기 관리",
                "guide_text": [
                    "줄기가 15~20cm 자라면 줄기 밑동 부분을 흙으로 덮어줍니다 (북주기).",
                    "흙이 마르지 않게 꾸준히 물을 줍니다. 과습에 주의하세요."
                ]
            },
            "개화": {
                "title": "감자 개화 관리",
                "guide_text": [
                    "꽃이 피는 시기는 감자가 커지는 중요한 시기입니다.",
                    "이 시기에는 물 관리에 특히 신경 써야 합니다."
                ]
            },
            "수확": {
                "title": "감자 수확",
                "guide_text": [
                    "잎과 줄기가 누렇게 변하고 시들기 시작하면 수확 시기입니다.",
                    "수확 1~2주 전에는 물 주는 것을 멈춰 저장성을 높일 수 있습니다.",
                    "흙을 조심스럽게 파서 감자를 캐냅니다."
                ]
            }
        },
        "detailed_guide": [],
        "expected_cultivation_days": 75
    }
]

_CROPS_DATA_MAP = {crop["id"]: crop for crop in CROPS_DATA}

def get_all_crops() -> List[Dict[str, Any]]:
    return CROPS_DATA

def get_crop_by_id(crop_id: str) -> Optional[Dict[str, Any]]:
    return _CROPS_DATA_MAP.get(crop_id)

def find_recommended_crops(duration: str, environment: str, region: str, limit: int = 5) -> List[Dict[str, Any]]:
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

agricultural_knowledge_base = {
    # ... (기존 지식 기반 내용은 유지) ...

    "질병 진단 기능": {
        "summary": "식물 잎사귀 이미지를 업로드하시면 AI가 질병 또는 해충을 진단하고 해결책을 안내해 드립니다.",
        "details": "초록손 앱의 질병 진단 기능을 통해 식물 잎, 줄기, 열매 등의 이상 증상 사진을 업로드해 보세요. 인공지능이 분석하여 예상되는 질병이나 해충의 종류, 심각도, 그리고 초기 방제 및 관리 방법을 알려드립니다. [질병 진단 바로가기] 버튼을 눌러 바로 이용하실 수 있습니다.",
        "link_keyword": "질병 진단", # ⭐ 추가: 프론트엔드에서 링크를 생성할 텍스트
        "link_page": "img.html" # ⭐ 수정: /PRH-002 -> img.html
    },
    "시뮬레이션 기능": {
        "summary": "농작물 시뮬레이션 기능으로 재배 환경에 따른 미래 생육 상태를 예측하고 시각화할 수 있습니다.",
        "details": "초록손 시뮬레이션 기능은 재배할 농작물 종류를 선택하고 온도, 습도, 일조량 등 환경 조건을 입력하면, 해당 조건에서 예상되는 작물의 성장 곡선, 예상 수확량 등을 예측하여 시각적으로 보여줍니다. 이를 통해 최적의 재배 조건을 찾아 성공적인 농사를 계획하는 데 도움을 받을 수 있습니다. [농작물 시뮬레이션 바로가기] 버튼을 클릭해 지금 바로 시작해 보세요!",
        "link_keyword": "농작물 시뮬레이션", # ⭐ 추가
        "link_page": "crop.html" # ⭐ 수정: /PRH-003 -> crop.html
    },
    "내 농장 확인": {
        "summary": "내 농장 기능을 통해 현재 키우시는 작물의 성장 진행도를 한눈에 확인하고 효율적으로 관리하세요.",
        "details": "초록손 앱의 '내 농장' 페이지에서는 등록된 작물들의 현재 생육 상태, 물 주기 알림, 병충해 발생 이력 등을 종합적으로 관리할 수 있습니다. 각 작물의 성장 일지를 기록하고, 필요할 때 맞춤형 가이드를 받아보세요. [내 농장 바로가기] 버튼을 눌러 이동하실 수 있습니다.",
        "link_keyword": "내 농장", # ⭐ 추가
        "link_page": "main.html" # ⭐ 수정: /my_farm_page_id -> main.html
    },
    "수확한 작물 확인": { # ⭐ 새로 추가할 페이지 정보
        "summary": "그동안 키웠던 작물들의 정보를 확인하실 수 있습니다.",
        "details": "재배를 완료하고 수확한 작물들의 재배 이력과 결과를 '수확한 작물' 페이지에서 확인해 보세요. 어떤 작물을 언제, 어떻게 키웠는지 기록을 보면서 다음 재배 계획을 세우는 데 도움을 받을 수 있습니다. [수확한 작물 바로가기] 버튼을 눌러 이동하실 수 있습니다.",
        "link_keyword": "수확한 작물", # ⭐ 추가
        "link_page": "harvested_crops.html" # ⭐ 새로운 페이지 URL
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