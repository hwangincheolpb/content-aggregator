"""Gemini API를 이용한 시황 요약 모듈"""
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Gemini API를 사용하여 시황 데이터 요약"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        초기화

        Args:
            api_key: Gemini API 키
            model_name: 사용할 Gemini 모델명
        """
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.max_retries = 3
        self.retry_delay = 2

        # 프롬프트 템플릿 (간결 버전)
        self.prompt_template = """당신은 신한투자증권 서울금융센터 황인철 PB의 '전용 시황 비서'입니다.
아래 시황 데이터를 바탕으로 고객에게 발송할 아침 시황 요약을 작성해주세요.

📌 양식 (반드시 준수):

📊 핵심 요약
- (첫 번째 핵심 이슈)
- (두 번째 핵심 이슈)
- (세 번째 핵심 이슈)

📈 주요 지수
• 다우: (종가) (등락률%)
• 나스닥: (종가) (등락률%)
• S&P 500: (종가) (등락률%)
• KOSPI 예상: (방향성)

💹 매크로 지표
• 달러인덱스: (수치) (등락)
• 원/달러: (수치) (등락)
• 국제유가: (수치) (등락)
• 10년물 금리: (수치) (등락)

⚠️ 작성 원칙:
- 이모지와 가독성 최우선
- 한글만 사용 (영어 표기 최소화)
- 결과물만 출력 (추가 설명 없이)
- 불필요한 인사말 없이 바로 시작

---
[시황 데이터]
{market_data}
"""

        # 프롬프트 템플릿 (상세 버전)
        self.detailed_prompt_template = """당신은 신한투자증권 서울금융센터 황인철 PB의 '전용 시황 비서'입니다.
아래 시황 데이터를 바탕으로 고객에게 발송할 아침 시황 요약을 작성해주세요.

📌 양식 (반드시 준수):

📊 핵심 요약
- (첫 번째 핵심 이슈)
- (두 번째 핵심 이슈)
- (세 번째 핵심 이슈)

📝 핵심 내용
• 시장 총평: (2-3문장으로 오늘 시장 요약)
• 주요 종목: (움직임이 컸던 종목들)
• 투자 심리: (공포/탐욕 지수, 시장 분위기)

📈 주요 지수
• 다우: (종가) (등락률%)
• 나스닥: (종가) (등락률%)
• S&P 500: (종가) (등락률%)
• 러셀 2000: (종가) (등락률%)
• KOSPI 예상: (방향성 및 근거)

💹 매크로 지표
• 달러인덱스: (수치) (등락)
• 원/달러: (수치) (등락)
• 국제유가(WTI): (수치) (등락)
• 금: (수치) (등락)
• 10년물 금리: (수치) (등락)
• VIX: (수치) (등락)

💡 오늘의 키워드
(시장을 움직인 핵심 키워드 2-3개와 간단한 설명)

⚠️ 작성 원칙:
- 이모지와 가독성 최우선
- 한글만 사용 (영어 표기 최소화)
- 결과물만 출력 (추가 설명 없이)
- 불필요한 인사말 없이 바로 시작

---
[시황 데이터]
{market_data}
"""

    def summarize(self, market_data: str, use_detailed: bool = False) -> Optional[str]:
        """
        시황 데이터 요약

        Args:
            market_data: 수집된 시황 데이터
            use_detailed: 상세 요약 사용 여부

        Returns:
            요약된 텍스트 또는 None (실패 시)
        """
        if not market_data or not market_data.strip():
            logger.error("요약할 데이터가 없음")
            return None

        # 프롬프트 선택
        template = self.detailed_prompt_template if use_detailed else self.prompt_template
        prompt = template.format(market_data=market_data)

        # 재시도 로직
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Gemini API 요약 시도 {attempt}/{self.max_retries}")

                response = self.model.generate_content(prompt)

                if response and response.text:
                    summary = response.text.strip()

                    # 응답 검증 (너무 짧으면 재시도)
                    if len(summary) < 100:
                        logger.warning(f"응답이 너무 짧음 ({len(summary)} 글자), 재시도...")
                        time.sleep(self.retry_delay * attempt)
                        continue

                    logger.info(f"요약 생성 성공: {len(summary)} 글자")
                    return summary
                else:
                    logger.warning("Gemini API 응답이 비어있음")

            except Exception as e:
                logger.error(f"Gemini API 호출 실패 (시도 {attempt}): {e}")

            # 재시도 전 대기 (지수 백오프)
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt
                logger.info(f"{wait_time}초 후 재시도...")
                time.sleep(wait_time)

        logger.error("모든 재시도 실패")
        return None

    def summarize_simple(self, market_data: str) -> Optional[str]:
        """간결한 요약 생성"""
        return self.summarize(market_data, use_detailed=False)

    def summarize_detailed(self, market_data: str) -> Optional[str]:
        """상세 요약 생성"""
        return self.summarize(market_data, use_detailed=True)


def test_gemini_summarizer():
    """테스트 함수"""
    import os
    logging.basicConfig(level=logging.INFO)

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("GEMINI_API_KEY 환경변수를 설정해주세요")
        return

    summarizer = GeminiSummarizer(api_key)

    test_data = """
    미국 증시 마감 시황

    S&P 500: 4,850.43 (+0.52%)
    나스닥: 15,310.97 (+0.83%)
    다우존스: 38,001.81 (+0.35%)

    미국 10년물 국채 금리: 4.12% (-0.03%p)
    달러인덱스: 103.25 (-0.15%)
    원달러 환율: 1,325.50 (-5.30원)

    WTI 유가: $75.32 (+1.2%)
    금: $2,025.40 (+0.3%)
    VIX: 13.25 (-0.45)

    주요 뉴스:
    - 연준 위원, 금리 인하 신중한 접근 시사
    - 애플 신제품 발표 예정으로 기술주 강세
    - 고용지표 예상 상회, 경기 연착륙 기대감
    """

    summary = summarizer.summarize(test_data)
    if summary:
        print("=" * 50)
        print("요약 결과:")
        print("=" * 50)
        print(summary)
    else:
        print("요약 실패")


if __name__ == '__main__':
    test_gemini_summarizer()
