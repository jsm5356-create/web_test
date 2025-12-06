import google.generativeai as genai
from typing import List, Dict
from datetime import datetime
import streamlit as st


def analyze_news_with_gemini(news_list: List[Dict], api_key: str) -> str:
    """
    뉴스 기사 리스트를 Gemini API로 분석하여 요약 보고서를 생성합니다.
    
    Args:
        news_list: 뉴스 기사 리스트
        api_key: Gemini API 키
        
    Returns:
        마크다운 형식의 요약 보고서
    """
    if not news_list:
        return "분석할 뉴스가 없습니다."
    
    # Gemini API 설정 (Gemini 2.0 Flash 사용)
    genai.configure(api_key=api_key)
    # Gemini 2.0 Flash 모델 사용 (더 빠르고 효율적)
    # 모델 이름 우선순위: gemini-2.0-flash > gemini-2.0-flash-exp > gemini-1.5-flash
    try:
        # 정식 버전인 2.0 Flash를 먼저 시도
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        try:
            # 실험 버전 시도
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception:
            # 최후의 수단으로 1.5 Flash 사용
            model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 뉴스 기사들을 텍스트로 변환
    news_text = ""
    for i, news in enumerate(news_list[:50], 1):  # 최대 50개만 처리
        summary = news.get('summary', '')
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        news_text += f"\n{i}. **{news['title']}**\n"
        news_text += f"   - 링크: {news['link']}\n"
        news_text += f"   - 요약: {summary}\n"
        news_text += f"   - 출처: {news.get('source', '알 수 없음')}\n"
        news_text += f"   - 발행일: {news['published']}\n"
    
    # 프롬프트 작성
    prompt = f"""다음은 오늘 수집된 IT/기술 뉴스 기사들입니다. 
이 뉴스들을 분석하여 마크다운 형식의 요약 보고서를 작성해주세요.

요구사항:
1. 주요 뉴스를 카테고리별로 분류하여 정리
2. 각 뉴스의 핵심 내용을 간결하게 요약
3. 마크다운 형식으로 작성 (제목, 리스트, 강조 등 활용)
4. 날짜별로 섹션을 나누어 정리
5. 한국어로 작성

뉴스 목록:
{news_text}

위 뉴스들을 분석한 요약 보고서를 작성해주세요:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API 오류: {e}")
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

