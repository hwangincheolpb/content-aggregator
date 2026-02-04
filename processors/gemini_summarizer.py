"""Gemini API를 이용한 시황 요약 모듈"""
import time
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Gemini API를 사용하여 시황 데이터 요약"""

    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
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

        # 프롬프트: 핵심 요약만 생성 (지수/매크로는 별도 삽입)
        self.analysis_prompt = """당신은 증권사 PB의 시황 비서입니다.
아래 시황 데이터에서 **핵심 이슈 3가지**와 **KOSPI 전망**만 추출해주세요.

📌 출력 양식 (정확히 준수):

📊 핵심 요약
- (첫 번째 핵심 이슈 - 한 문장)
- (두 번째 핵심 이슈 - 한 문장)
- (세 번째 핵심 이슈 - 한 문장)

🇰🇷 KOSPI 전망
(오늘 한국 증시 예상 방향과 근거 1-2문장)

⚠️ 규칙:
- 위 양식만 출력 (다른 내용 절대 금지)
- 숫자/지수/환율 언급 금지 (별도 제공됨)
- 한글만 사용
- 인사말 없이 바로 시작

---
[시황 데이터]
{market_data}
"""

    def summarize(self, market_data: str, market_quotes: Optional[Dict] = None, use_detailed: bool = False) -> Optional[str]:
        """
        시황 데이터 요약 (Yahoo 지수는 고정 삽입)

        Args:
            market_data: 수집된 시황 데이터
            market_quotes: Yahoo Finance에서 가져온 지수 데이터
            use_detailed: 상세 요약 사용 여부

        Returns:
            요약된 텍스트 또는 None (실패 시)
        """
        if not market_data or not market_data.strip():
            logger.error("요약할 데이터가 없음")
            return None

        # Gemini로 핵심 요약만 생성
        prompt = self.analysis_prompt.format(market_data=market_data)
        analysis = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Gemini API 요약 시도 {attempt}/{self.max_retries}")
                response = self.model.generate_content(prompt)

                if response and response.text:
                    analysis = response.text.strip()
                    if len(analysis) >= 50:
                        logger.info(f"분석 생성 성공: {len(analysis)} 글자")
                        break
                    logger.warning(f"응답이 너무 짧음 ({len(analysis)} 글자)")

            except Exception as e:
                logger.error(f"Gemini API 호출 실패 (시도 {attempt}): {e}")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        if not analysis:
            logger.error("분석 생성 실패")
            return None

        # Yahoo 지수 데이터가 있으면 고정 포맷으로 조합
        if market_quotes:
            summary = self._build_final_summary(analysis, market_quotes, use_detailed)
        else:
            summary = analysis

        return summary

    def _build_final_summary(self, analysis: str, quotes: Dict, use_detailed: bool) -> str:
        """분석 결과와 Yahoo 지수를 조합하여 최종 요약 생성"""

        def fmt(symbol: str, is_rate: bool = False, is_krw: bool = False) -> str:
            """지표 포맷팅"""
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            price = q['price']
            pct = q['change_pct']
            direction = "▲" if pct >= 0 else "▼"

            if is_rate:
                return f"{price:.2f}% ({direction}{abs(pct):.2f}%)"
            elif is_krw:
                return f"{price:,.0f}원 ({direction}{abs(pct):.2f}%)"
            elif price > 1000:
                return f"{price:,.2f} ({direction}{abs(pct):.2f}%)"
            else:
                return f"{price:.2f} ({direction}{abs(pct):.2f}%)"

        # 지수 섹션
        index_section = f"""📈 주요 지수
• 다우: {fmt('^DJI')}
• S&P 500: {fmt('^GSPC')}
• 나스닥: {fmt('^IXIC')}"""

        if use_detailed:
            index_section += f"\n• 러셀 2000: {fmt('^RUT')}"

        # 매크로 섹션
        def fmt_oil(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            direction = "▲" if q['change_pct'] >= 0 else "▼"
            return f"${q['price']:.2f} ({direction}{abs(q['change_pct']):.2f}%)"

        macro_section = f"""💹 매크로 지표
• 달러인덱스: {fmt('DX-Y.NYB')}
• 원/달러: {fmt('KRW=X', is_krw=True)}
• WTI 유가: {fmt_oil('CL=F')}
• 10년물 금리: {fmt('^TNX', is_rate=True)}"""

        if use_detailed:
            macro_section += f"\n• 금: {fmt('GC=F')}"
            macro_section += f"\n• VIX: {fmt('^VIX')}"

        # 최종 조합
        final = f"""{analysis}

{index_section}

{macro_section}"""

        return final

    def summarize_simple(self, market_data: str, market_quotes: Optional[Dict] = None) -> Optional[str]:
        """간결한 요약 생성"""
        return self.summarize(market_data, market_quotes, use_detailed=False)

    def summarize_detailed(self, market_data: str, market_quotes: Optional[Dict] = None) -> Optional[str]:
        """상세 요약 생성"""
        return self.summarize(market_data, market_quotes, use_detailed=True)


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
