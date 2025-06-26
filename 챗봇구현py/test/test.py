# test.py (Streamlit 앱의 최종 실행 파일)

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from docx import Document # pip install python-docx 필요

# --- 전역 설정 및 지식 데이터베이스 ---
# .env 파일에서 API 키 로드
load_dotenv(dotenv_path='test.env')
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# API 키가 없으면 Streamlit 앱이 실행되지 않도록 함
# (Streamlit 컨텍스트 밖에서는 raise ValueError, Streamlit 컨텍스트 안에서는 st.error + st.stop())
if not GOOGLE_API_KEY:
    # 이 부분은 Streamlit 앱 시작 전 검사이므로, 여기서는 Value Error 발생.
    # Streamlit 앱 내부에서 오류 처리할 때는 st.error를 사용.
    raise ValueError("Google API 키가 설정되지 않았습니다. test.env 파일을 확인해주세요.")

genai.configure(api_key=GOOGLE_API_KEY)

# Gemini Pro 모델 초기화
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    # 이 부분도 Streamlit 앱 시작 전 오류 가능성이 있으므로, 초기 로딩 시 문제가 생기면 종료
    raise Exception(f"Gemini Pro 모델 초기화 실패: {e}")

# 지식 데이터베이스 (농업 정보)
agricultural_knowledge_base = {
    "상추 재배 방법": "상추는 서늘하고 햇볕이 잘 드는 곳에서 잘 자랍니다. 씨앗을 심고 싹이 나면 솎아주세요. 물은 흙이 마르지 않게 꾸준히 주는 것이 중요합니다.",
    "토마토 병충해": "토마토에 흔한 병충해로는 탄저병, 역병, 온실가루이 등이 있습니다. 각 병충해에 맞는 방제법을 사용해야 합니다.",
    "딸기 수확 시기": "딸기는 보통 4월에서 6월 사이에 수확하며, 품종과 재배 환경에 따라 달라질 수 있습니다.",
    "스마트팜이란?": "스마트팜은 정보통신기술(ICT)을 활용하여 작물 생육 환경을 원격 및 자동으로 제어하는 농업 시스템입니다.",
    "온도 조절 중요성": "작물 생육에 있어 온도는 매우 중요합니다. 너무 높거나 낮은 온도는 작물의 스트레스를 유발하고 성장을 저해할 수 있습니다.",
    "질병 진단 기능": "식물 잎사귀 이미지를 업로드하면 질병 또는 해충을 진단해 드립니다. [질병 진단 바로가기](/PRH-002)",
    "시뮬레이션 기능": "재배할 농작물 종류를 선택하고 환경 조건(온도, 습도, 일조량 등)을 입력하면 미래 생육 상태(예상 수확량, 성장 곡선)를 예측하여 시각화해야 한다. [농작물 시뮬레이션 바로가기](/PRH-003)",
    "내 농장 확인": "현재 키우시는 작물의 성장 진행도를 한 눈에 확인하고 관리할 수 있습니다. [내 농장 바로가기](/my_farm_page_id)",
    "엑셀 보고서": "엑셀 보고서 생성을 요청하셨습니다. 'generate_excel_report' 함수를 호출합니다.",
    "워드 보고서": "워드 보고서 생성을 요청하셨습니다. 'generate_word_report' 함수를 호출합니다."
}

# --- 챗봇 핵심 함수 정의 ---

def generate_excel_report(query_text):
    """
    사용자 질의에 기반하여 간단한 엑셀 보고서를 생성합니다.
    실제 데이터는 DB에서 가져와야 합니다.
    """
    try:
        data = {
            '날짜': [f'2025-06-{i:02d}' for i in range(10, 17)],
            '상추_성장(cm)': [5, 6, 7.5, 8, 9, 9.5, 10],
            '온도(℃)': [22, 23, 21, 24, 23, 22, 25],
            '습도(%)': [60, 62, 58, 65, 63, 61, 64]
        }
        df = pd.DataFrame(data)

        file_name = f"상추_성장_보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(file_name, index=False)
        return f"요청하신 엑셀 보고서 '{file_name}'가 성공적으로 생성되었습니다. 파일을 다운로드할 수 있습니다."
    except Exception as e:
        return f"엑셀 보고서 생성 중 오류가 발생했습니다: {e}"

def generate_word_report(query_text):
    """
    사용자 질의에 기반하여 간단한 워드 보고서를 생성합니다.
    docx 라이브러리가 필요합니다. (pip install python-docx)
    """
    try:
        document = Document()
        document.add_heading('농작물 성장 보고서', level=1)
        document.add_paragraph(f'생성 날짜: {datetime.now().strftime("%Y년 %m월 %d일")}')
        document.add_heading('1. 상추 성장 개요', level=2)
        document.add_paragraph('이 보고서는 특정 기간 동안의 상추 성장 데이터를 요약합니다. 데이터는 센서 모니터링 시스템에서 수집되었습니다.')
        document.add_heading('2. 주요 데이터', level=2)
        data = {
            '날짜': [f'2025-06-{i:02d}' for i in range(10, 17)],
            '상추_성장(cm)': [5, 6, 7.5, 8, 9, 9.5, 10],
            '온도(℃)': [22, 23, 21, 24, 23, 22, 25],
            '습도(%)': [60, 62, 58, 65, 63, 61, 64]
        }
        df = pd.DataFrame(data)
        document.add_paragraph(df.to_string())
        file_name = f"농작물_성장_보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        document.save(file_name)
        return f"요청하신 워드 보고서 '{file_name}'가 성공적으로 생성되었습니다. 파일을 다운로드할 수 있습니다."
    except ImportError:
        return "docx 라이브러리가 설치되지 않았습니다. 'pip install python-docx'를 실행하여 설치해주세요."
    except Exception as e:
        return f"워드 보고서 생성 중 오류가 발생했습니다: {e}"

def get_chatbot_response(user_query):
    """
    사용자의 질문에 따라 챗봇 응답을 생성하고,
    필요 시 특정 기능 링크 또는 파일 생성 로직을 트리거합니다.
    """
    prompt = f"""
    당신은 스마트 농업 도우미 챗봇입니다. 사용자의 질문에 대해 친절하게 답변하고,
    필요 시 다른 기능(농작물 시뮬레이션, 질병 진단, 내 농장)으로의 링크를 안내합니다.
    만약 보고서나 엑셀 파일 생성을 요청하는 경우, 해당 기능을 수행해야 합니다.

    [농업 정보 제공 예시]
    질문: 상추는 어떻게 키우나요?
    답변: 상추는 서늘하고 햇볕이 잘 드는 곳에서 잘 자랍니다. 씨앗을 심고 싹이 나면 솎아주세요. 물은 흙이 마르지 않게 꾸준히 주는 것이 중요합니다.

    [기능 링크 제공 예시]
    질문: 상추가 시들시들해요. 왜 그런가요?
    답변: 상추의 상태를 정확히 진단하려면 질병 진단 기능을 사용해 보세요. [질병 진단 바로가기](http://localhost:8080/PRH-002)
    질문: 상추를 키우면 수확량이 얼마나 될까요?
    답변: 예상 수확량을 확인하려면 농작물 시뮬레이션 기능을 이용해 보세요. [농작물 시뮬레이션 바로가기](http://localhost:8080/PRH-003)
    질문: 제가 키우고 있는 상추 상태를 보고 싶어요.
    답변: 현재 키우시는 작물 상태는 '내 농장' 페이지에서 확인하실 수 있습니다. [내 농장 바로가기](http://localhost:8080/my_farm_page_id)

    [보고서/엑셀 생성 예시]
    질문: 지난주 상추 성장 데이터를 엑셀로 정리해줘.
    답변: 엑셀 파일 생성을 요청하셨습니다. 'generate_excel_report' 함수를 호출합니다. (실제로는 함수 호출 메시지를 파싱하여 처리)
    질문: 이번 달 농작물 보고서를 워드 파일로 만들어줘.
    답변: 보고서 생성을 요청하셨습니다. 'generate_word_report' 함수를 호출합니다. (실제로는 함수 호출 메시지를 파싱하여 처리)

    사용자 질문: {user_query}
    답변:
    """

    try:
        response = model.generate_content(prompt)
        generated_text = response.text

        # --- 여기서 의도 분류 및 기능 호출 로직 추가 ---
        # 1. 농업 정보 질문 (기본) - 지식 베이스 검색 또는 LLM 직접 답변
        for keyword, answer in agricultural_knowledge_base.items():
            if keyword in user_query:
                return answer

        # 2. 기능 링크 연결 (보고서 참조)
        if "질병 진단" in user_query or "시들" in user_query or "병충해" in user_query or "잎사귀 이미지" in user_query:
            return f"네, 식물 잎사귀 이미지를 통해 질병 진단을 도와드릴 수 있습니다. [질병 진단 바로가기](http://localhost:8080/PRH-002)"
        elif "시뮬레이션" in user_query or "수확량" in user_query or "성장 예측" in user_query or "환경 조건" in user_query:
            return f"재배할 농작물 종류와 환경 조건을 입력하시면 미래 생육 상태를 예측해 드립니다. [농작물 시뮬레이션 바로가기](http://localhost:8080/PRH-003)"
        elif "내 농장" in user_query or "얼마나 컸는지" in user_query or "상태 확인" in user_query or "성장 진행도" in user_query:
            return f"현재 키우시는 작물의 성장 진행도는 '내 농장' 페이지에서 확인하실 수 있습니다. [내 농장 바로가기](http://localhost:8080/my_farm_page_id)"

        # 3. 보고서/엑셀 생성 기능 호출
        if ("엑셀" in user_query or "excel" in user_query) and ("생성" in user_query or "만들어" in user_query or "정리" in user_query):
            return generate_excel_report(user_query)
        elif ("보고서" in user_query or "report" in user_query) and ("생성" in user_query or "만들어" in user_query or "워드" in user_query or "word" in user_query):
            return generate_word_report(user_query)

        return generated_text.strip()

    except Exception as e:
        return f"죄송합니다. 질문 처리 중 오류가 발생했습니다: {e}"

# --- Streamlit UI 구성 (if __name__ == "__main__": 블록 안에) ---
if __name__ == "__main__":
    st.set_page_config(page_title="스마트 농업 도우미 챗봇", page_icon="🌿")
    st.title("🌱 스마트 농업 도우미 챗봇")
    st.write("농작물 재배, 질병, 환경 제어 등 궁금한 점을 저에게 물어보세요!")

    # 챗봇 대화 기록 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 대화 기록 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("여기에 질문을 입력하세요..."):
        # 사용자 메시지 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 챗봇 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = get_chatbot_response(prompt)
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        # 파일 생성 요청이 있었다면 다운로드 버튼 제공
        if "성공적으로 생성되었습니다." in response and ("엑셀" in prompt or "워드" in prompt):
            file_name_match = None
            if "엑셀" in prompt:
                import re
                match = re.search(r"'(상추_성장_보고서_\d{8}_\d{6}\.xlsx)'", response)
                if match:
                    file_name_match = match.group(1)
            elif "워드" in prompt:
                import re
                match = re.search(r"'(농작물_성장_보고서_\d{8}_\d{6}\.docx)'", response)
                if match:
                    file_name_match = match.group(1)

            if file_name_match and os.path.exists(file_name_match):
                with open(file_name_match, "rb") as file:
                    st.download_button(
                        label=f"{file_name_match} 다운로드",
                        data=file,
                        file_name=file_name_match,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if "xlsx" in file_name_match else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                # 다운로드 후 파일 정리 (선택 사항)
                # os.remove(file_name_match)