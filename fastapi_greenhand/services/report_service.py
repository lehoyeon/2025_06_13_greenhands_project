# services/report_service.py
import os
import pandas as pd
from datetime import datetime
from docx import Document
import re
import logging
from fastapi import HTTPException
from typing import Optional

from config import REPORT_DIR

def generate_excel_report(subject: str = "농작물", content_for_report: Optional[str] = None):
    try:
        file_base_name = f"{subject}_관련_정보_요약"
        file_name = os.path.join(REPORT_DIR, f"{file_base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        # 실제 데이터가 있다면 DataFrame에 채워야 합니다.
        # 예시: pd.DataFrame({'Summary': [content_for_report]}).to_excel(file_name, index=False)
        pd.DataFrame().to_excel(file_name, index=False) 

        message = (
            f"요청하신 엑셀 보고서 '{os.path.basename(file_name)}'가 성공적으로 생성되었습니다."
            f"\n하지만 엑셀 보고서는 표 형식의 데이터를 기반으로 하므로, "
            f"현재 시스템에서는 **주요 정보 요약(텍스트)만 포함되어 있거나, 데이터가 비어 있을 수 있습니다.**"
            f"\n상세한 텍스트 정보는 워드 보고서로 요청하시는 것을 추천합니다."
        )

        return {"message": message, "file_path": f"/reports_static/{os.path.basename(file_name)}"}
    except Exception as e:
        logging.error(f"Error generating excel report: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"엑셀 보고서 생성 중 예기치 않은 오류 발생: {e}")

def generate_word_report(subject: str = "농작물", content_for_report: Optional[str] = None):
    try:
        document = Document()
        document.add_heading(f'{subject} 정보 보고서', level=1)
        document.add_paragraph(f'생성 날짜: {datetime.now().strftime("%Y년 %m월 %d일")}')
        
        if content_for_report:
            document.add_heading('1. 요청하신 정보 요약', level=2)
            # HTML 링크 제거 (보고서에 적합하게)
            clean_content = re.sub(r'<a href=".*?\" class="link-button".*?>(.*?)</a>', r'\1', content_for_report)
            for paragraph in clean_content.split('\n'):
                if paragraph.strip():
                    document.add_paragraph(paragraph.strip())
        else:
            document.add_heading('1. 일반 농작물 정보', level=2)
            document.add_paragraph('이 보고서는 요청하신 내용에 대한 일반적인 정보를 포함합니다.')
            document.add_paragraph('구체적인 정보는 챗봇과의 대화 기록을 참고하시거나, 질문 시 더 자세히 말씀해주세요.')
            
        file_name = os.path.join(REPORT_DIR, f"{subject}_정보_보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        document.save(file_name)
        
        message = f"요청하신 워드 보고서 '{os.path.basename(file_name)}'가 성공적으로 생성되었습니다."
        return {"message": message, "file_path": f"/reports_static/{os.path.basename(file_name)}"}
    except ImportError:
        logging.error("Error: 'python-docx' library not installed. Please run 'pip install python-docx'.")
        raise HTTPException(status_code=500, detail="docx 라이브러리가 설치되지 않았습니다. 'pip install python-docx'를 실행하여 설치해주세요.")
    except Exception as e:
        logging.error(f"Error generating word report: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"워드 보고서 생성 중 예기치 않은 오류 발생: {e}")