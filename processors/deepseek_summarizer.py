"""DeepSeek API를 이용한 요약 모듈 (OpenAI 호환)"""
import time
from typing import Optional, Dict
import logging
import requests

logger = logging.getLogger(__name__)


class DeepSeekSummarizer:
    """DeepSeek API를 사용하여 콘텐츠 요약"""

    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        """
        초기화

        Args:
            api_key: DeepSeek API 키
            model_name: 사용할 모델명 (deepseek-chat 또는 deepseek-reasoner)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.max_retries = 3
        self.retry_delay = 2

    def _call_api(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """DeepSeek API 호출"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"DeepSeek API 호출 시도 {attempt}/{self.max_retries}")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()

                result = response.json()
                content = result['choices'][0]['message']['content']

                if content and len(content) >= 50:
                    logger.info(f"응답 성공: {len(content)} 글자")
                    return content.strip()

                logger.warning(f"응답이 너무 짧음 ({len(content) if content else 0} 글자)")

            except requests.exceptions.RequestException as e:
                logger.error(f"API 호출 실패 (시도 {attempt}): {e}")
            except (KeyError, IndexError) as e:
                logger.error(f"응답 파싱 실패 (시도 {attempt}): {e}")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        return None


class DeepSeekMarketSummarizer(DeepSeekSummarizer):
    """시황 요약 전용"""

    def __init__(self, api_key: str):
        super().__init__(api_key, model_name="deepseek-chat")

        self.analysis_prompt = """당신은 증권사 PB의 시황 비서입니다.
아래 시황 데이터를 분석하여 아래 양식대로 요약해주세요.

📌 출력 양식 (정확히 준수):

🇺🇸 {날짜} 미국 증시: {한 줄 헤드라인}

- {첫 번째 핵심 포인트 - 한 문장}
- {두 번째 핵심 포인트 - 한 문장}
- {세 번째 핵심 포인트 - 한 문장}

✅ 핵심 내용

시장 총평: {전반적인 시장 흐름과 배경 - 2~3문장}

주요 종목: {개별 종목 동향과 이유 - 2~3문장}

투자 심리: {투자 심리 및 한국 증시 전망 - 2~3문장}

⚠️ 규칙:
- 위 양식만 출력 (지수/지표 섹션은 별도 추가됨)
- 날짜는 "2026년 X월 X일" 형식
- 전문적이지만 읽기 쉬운 문체
- 인사말/서명 없이 바로 시작
- 한글만 사용"""

    def summarize(self, market_data: str, market_quotes: Optional[Dict] = None, use_detailed: bool = False) -> Optional[str]:
        """
        시황 데이터 요약 (2단계: 1차 요약 → 2차 다듬기)

        Args:
            market_data: 수집된 시황 데이터
            market_quotes: Yahoo Finance에서 가져온 지수 데이터
            use_detailed: 상세 요약 사용 여부

        Returns:
            요약된 텍스트 또는 None
        """
        if not market_data or not market_data.strip():
            logger.error("요약할 데이터가 없음")
            return None

        # 1단계: 초안 생성
        prompt = f"{self.analysis_prompt}\n\n---\n[시황 데이터]\n{market_data}"
        draft = self._call_api(prompt)

        if not draft:
            logger.error("1단계 분석 생성 실패")
            return None

        logger.info(f"1단계 초안 생성 완료: {len(draft)} 글자")

        # 2단계: 문체 다듬기 + 검증
        refined = self._refine_summary(draft)

        if market_quotes:
            return self._build_final_summary(refined, market_quotes, use_detailed)
        return refined

    def _refine_summary(self, draft: str) -> str:
        """2단계: 문체 다듬기 및 검증"""
        refine_prompt = """아래 증권 시황 요약문의 문체를 다듬어주세요.

📌 수정 기준:
1. 자연스럽고 전문적인 한국어 문체 (번역투 제거)
2. "~되었습니다", "~보였습니다" 등 정중하지만 간결한 어미
3. 불필요한 수식어 제거, 핵심 정보 중심
4. 문장이 너무 길면 분리
5. 원문 구조와 내용은 유지

원문:
{draft}

---
다듬어진 버전만 출력 (설명 없이):"""

        refined = self._call_api(refine_prompt.format(draft=draft))

        if refined and len(refined) >= 100:
            logger.info(f"2단계 다듬기 완료: {len(refined)} 글자")
            return refined

        logger.warning("2단계 다듬기 실패, 원본 사용")
        return draft

    def _build_final_summary(self, analysis: str, quotes: Dict, use_detailed: bool) -> str:
        """분석 결과와 Yahoo 지수를 조합하여 최종 요약 생성 (PB 형식)"""

        def fmt_index(symbol: str) -> str:
            """지수 포맷팅 (가격 + 등락률)"""
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            price = q['price']
            pct = q['change_pct']
            sign = "+" if pct >= 0 else ""
            return f"{price:,.2f} ({sign}{pct:.2f}%)"

        def fmt_rate(symbol: str) -> str:
            """금리 포맷팅"""
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            return f"{q['price']:.2f}%"

        def fmt_dollar(symbol: str) -> str:
            """달러 가격 포맷팅"""
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            pct = q['change_pct']
            sign = "+" if pct >= 0 else ""
            return f"{q['price']:.2f} ({sign}{pct:.2f}%)"

        def fmt_oil(symbol: str) -> str:
            """유가 포맷팅"""
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            pct = q['change_pct']
            sign = "+" if pct >= 0 else ""
            return f"{q['price']:.2f}달러 ({sign}{pct:.2f}%)"

        def fmt_vix(symbol: str) -> str:
            """VIX 포맷팅"""
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            pct = q['change_pct']
            sign = "+" if pct >= 0 else ""
            return f"{q['price']:.2f} ({sign}{pct:.2f}%)"

        # 주요 지수 섹션
        index_section = f"""📊 주요 지수

다우 {fmt_index('^DJI')}
나스닥 {fmt_index('^IXIC')}
S&P 500 {fmt_index('^GSPC')}
MSCI 한국(EWY) {fmt_index('EWY')}"""

        # 매크로 지표 섹션
        macro_section = f"""📉 매크로 지표

달러인덱스: {fmt_dollar('DX-Y.NYB')}
국제유가(WTI): {fmt_oil('CL=F')}
10년물 금리: {fmt_rate('^TNX')}
변동성(VIX): {fmt_vix('^VIX')}"""

        # 최종 조합 (PB 형식)
        return f"""신한투자증권 서울금융센터 황인철PB입니다.

{analysis}

{index_section}

{macro_section}

감사합니다."""


class DeepSeekContentSummarizer(DeepSeekSummarizer):
    """콘텐츠 요약 전용 (Content Aggregator용)"""

    def __init__(self, api_key: str):
        super().__init__(api_key, model_name="deepseek-chat")

    def summarize(self, items: list) -> Optional[str]:
        """
        수집된 콘텐츠 요약

        Args:
            items: 수집된 콘텐츠 리스트

        Returns:
            요약된 텍스트
        """
        if not items:
            logger.error("요약할 콘텐츠가 없음")
            return None

        # 콘텐츠 포맷팅
        content_text = self._format_items(items)

        system_prompt = """당신은 콘텐츠 큐레이터입니다.
수집된 콘텐츠를 분석하여 핵심 트렌드와 주요 내용을 한국어로 요약해주세요.

출력 양식:
## 🔥 오늘의 핵심 트렌드
(가장 중요한 3-5개 트렌드)

## 📰 주요 뉴스/글
(카테고리별 핵심 내용)

## 💡 주목할 포인트
(인사이트 또는 액션 아이템)"""

        prompt = f"아래 콘텐츠를 요약해주세요:\n\n{content_text}"
        return self._call_api(prompt, system_prompt)

    def _format_items(self, items: list, max_items: int = 50) -> str:
        """콘텐츠 아이템을 텍스트로 포맷팅"""
        lines = []
        for i, item in enumerate(items[:max_items], 1):
            source = item.get('source', 'Unknown')
            title = item.get('title', 'No title')
            summary = item.get('summary', '')[:200]
            lines.append(f"[{i}] [{source}] {title}\n{summary}\n")
        return '\n'.join(lines)

    def estimate_cost(self, items: list) -> float:
        """예상 비용 계산 (DeepSeek 기준)"""
        text = self._format_items(items)
        # 대략 4자 = 1토큰
        input_tokens = len(text) / 4
        output_tokens = 1000  # 예상 출력
        # DeepSeek: $0.14/1M input, $0.28/1M output
        cost = (input_tokens * 0.14 + output_tokens * 0.28) / 1_000_000
        return cost


class OpenRouterSummarizer:
    """OpenRouter API를 사용한 요약 (백업용, 여러 모델 지원)"""

    def __init__(self, api_key: str, model_name: str = "mistralai/mistral-small"):
        """
        초기화

        Args:
            api_key: OpenRouter API 키
            model_name: 사용할 모델 (mistralai/mistral-small, anthropic/claude-3-haiku 등)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.max_retries = 3
        self.retry_delay = 2

    def _call_api(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """OpenRouter API 호출"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/content-aggregator",
            "X-Title": "Content Aggregator"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"OpenRouter API 호출 시도 {attempt}/{self.max_retries} (모델: {self.model_name})")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()

                result = response.json()
                content = result['choices'][0]['message']['content']

                if content and len(content) >= 50:
                    logger.info(f"응답 성공: {len(content)} 글자")
                    return content.strip()

                logger.warning(f"응답이 너무 짧음 ({len(content) if content else 0} 글자)")

            except requests.exceptions.RequestException as e:
                logger.error(f"API 호출 실패 (시도 {attempt}): {e}")
            except (KeyError, IndexError) as e:
                logger.error(f"응답 파싱 실패 (시도 {attempt}): {e}")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        return None


class OpenRouterMarketSummarizer(OpenRouterSummarizer):
    """시황 요약 전용 (OpenRouter)"""

    def __init__(self, api_key: str, model_name: str = "mistralai/mistral-small"):
        super().__init__(api_key, model_name)

        self.analysis_prompt = """당신은 증권사 PB의 시황 비서입니다.
아래 시황 데이터를 분석하여 아래 양식대로 요약해주세요.

📌 출력 양식 (정확히 준수):

🇺🇸 {날짜} 미국 증시: {한 줄 헤드라인}

- {첫 번째 핵심 포인트 - 한 문장}
- {두 번째 핵심 포인트 - 한 문장}
- {세 번째 핵심 포인트 - 한 문장}

✅ 핵심 내용

시장 총평: {전반적인 시장 흐름과 배경 - 2~3문장}

주요 종목: {개별 종목 동향과 이유 - 2~3문장}

투자 심리: {투자 심리 및 한국 증시 전망 - 2~3문장}

⚠️ 규칙:
- 위 양식만 출력 (지수/지표 섹션은 별도 추가됨)
- 날짜는 "2026년 X월 X일" 형식
- 전문적이지만 읽기 쉬운 문체
- 인사말/서명 없이 바로 시작
- 한글만 사용"""

    def summarize(self, market_data: str, market_quotes: Optional[Dict] = None, use_detailed: bool = False) -> Optional[str]:
        """시황 데이터 요약 (2단계: 1차 요약 → 2차 다듬기)"""
        if not market_data or not market_data.strip():
            logger.error("요약할 데이터가 없음")
            return None

        # 1단계: 초안 생성
        prompt = f"{self.analysis_prompt}\n\n---\n[시황 데이터]\n{market_data}"
        draft = self._call_api(prompt)

        if not draft:
            logger.error("1단계 분석 생성 실패")
            return None

        logger.info(f"1단계 초안 생성 완료: {len(draft)} 글자")

        # 2단계: 문체 다듬기 + 검증
        refined = self._refine_summary(draft)

        if market_quotes:
            return self._build_final_summary(refined, market_quotes, use_detailed)
        return refined

    def _refine_summary(self, draft: str) -> str:
        """2단계: 문체 다듬기 및 검증"""
        refine_prompt = """아래 증권 시황 요약문의 문체를 다듬어주세요.

📌 수정 기준:
1. 자연스럽고 전문적인 한국어 문체 (번역투 제거)
2. "~되었습니다", "~보였습니다" 등 정중하지만 간결한 어미
3. 불필요한 수식어 제거, 핵심 정보 중심
4. 문장이 너무 길면 분리
5. 원문 구조와 내용은 유지

원문:
{draft}

---
다듬어진 버전만 출력 (설명 없이):"""

        refined = self._call_api(refine_prompt.format(draft=draft))

        if refined and len(refined) >= 100:
            logger.info(f"2단계 다듬기 완료: {len(refined)} 글자")
            return refined

        logger.warning("2단계 다듬기 실패, 원본 사용")
        return draft

    def _build_final_summary(self, analysis: str, quotes: Dict, use_detailed: bool) -> str:
        """분석 결과와 Yahoo 지수를 조합 (PB 형식)"""

        def fmt_index(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            pct = q['change_pct']
            sign = "+" if pct >= 0 else ""
            return f"{q['price']:,.2f} ({sign}{pct:.2f}%)"

        def fmt_rate(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            return f"{quotes[symbol]['price']:.2f}%"

        def fmt_dollar(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            sign = "+" if q['change_pct'] >= 0 else ""
            return f"{q['price']:.2f} ({sign}{q['change_pct']:.2f}%)"

        def fmt_oil(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            sign = "+" if q['change_pct'] >= 0 else ""
            return f"{q['price']:.2f}달러 ({sign}{q['change_pct']:.2f}%)"

        def fmt_vix(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            sign = "+" if q['change_pct'] >= 0 else ""
            return f"{q['price']:.2f} ({sign}{q['change_pct']:.2f}%)"

        index_section = f"""📊 주요 지수

다우 {fmt_index('^DJI')}
나스닥 {fmt_index('^IXIC')}
S&P 500 {fmt_index('^GSPC')}
MSCI 한국(EWY) {fmt_index('EWY')}"""

        macro_section = f"""📉 매크로 지표

달러인덱스: {fmt_dollar('DX-Y.NYB')}
국제유가(WTI): {fmt_oil('CL=F')}
10년물 금리: {fmt_rate('^TNX')}
변동성(VIX): {fmt_vix('^VIX')}"""

        return f"""신한투자증권 서울금융센터 황인철PB입니다.

{analysis}

{index_section}

{macro_section}

감사합니다."""


def test_deepseek():
    """테스트 함수"""
    import os
    logging.basicConfig(level=logging.INFO)

    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("DEEPSEEK_API_KEY 환경변수를 설정해주세요")
        return

    summarizer = DeepSeekMarketSummarizer(api_key)

    test_data = """
    미국 증시 마감 시황
    S&P 500: 4,850.43 (+0.52%)
    나스닥: 15,310.97 (+0.83%)

    주요 뉴스:
    - 연준 위원, 금리 인하 신중한 접근 시사
    - 애플 신제품 발표 예정으로 기술주 강세
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
    test_deepseek()
