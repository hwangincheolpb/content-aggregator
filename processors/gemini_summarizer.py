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

        # 프롬프트 템플릿
        self.prompt_template = """다음은 오늘 미국 마감 시황 데이터입니다.
한국어로 간결하고 이해하기 쉽게 요약해주세요.

## 요약 형식:
1. **시장 요약** (2-3문장으로 오늘 시장 핵심 정리)
2. **주요 지수**
   - S&P 500, 나스닥, 다우존스 등 변동률
3. **매크로 지표**
   - 금리, 환율(달러), 유가, 금 가격 등
4. **특이사항** (있는 경우만)
   - 급등락 종목, 주요 이벤트 등

## 주의사항:
- 불필요한 인사말이나 서두 없이 바로 내용 시작
- 숫자는 소수점 2자리까지만 표기
- 전일 대비 변동은 % 또는 포인트로 명확히 표기
- 결과물만 출력 (코멘트 없이)

---

[시황 데이터]
{market_data}
"""

        self.detailed_prompt_template = """다음은 오늘 미국 마감 시황 데이터입니다.
한국어로 상세하게 요약해주세요.

## 요약 형식:
1. **핵심 요약** (오늘 시장의 핵심 포인트 3-4개)
2. **주요 지수 현황**
   - S&P 500: 종가, 변동률
   - 나스닥: 종가, 변동률
   - 다우존스: 종가, 변동률
   - 러셀 2000: 종가, 변동률 (있는 경우)
3. **섹터별 동향**
   - 강세 섹터
   - 약세 섹터
4. **매크로 지표**
   - 미국 국채 금리 (10년물)
   - 달러 인덱스 / 원달러 환율
   - WTI 유가
   - 금 가격
   - VIX 지수
5. **주요 이슈 및 특이사항**
   - 시장에 영향을 준 주요 뉴스
   - 급등락 종목 (있는 경우)
6. **내일 전망** (간략하게)

## 주의사항:
- 불필요한 인사말이나 서두 없이 바로 내용 시작
- 숫자는 소수점 2자리까지만 표기
- 전일 대비 변동은 % 또는 포인트로 명확히 표기
- 결과물만 출력

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
