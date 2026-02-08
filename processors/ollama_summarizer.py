"""Ollama 로컬 LLM을 이용한 요약 모듈"""
import time
from typing import Optional, Dict
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/chat"


class OllamaMarketSummarizer:
    """Ollama qwen3:32b를 사용한 시황 요약"""

    def __init__(self, model_name: str = "qwen3:32b", base_url: str = OLLAMA_API_URL):
        self.model_name = model_name
        self.base_url = base_url
        self.max_retries = 2
        self.retry_delay = 5

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

    def _call_api(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Ollama API 호출 (chat endpoint)"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2000,
            },
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Ollama API 호출 시도 {attempt}/{self.max_retries} (모델: {self.model_name})")
                response = requests.post(
                    self.base_url,
                    json=payload,
                    timeout=300,  # 로컬 LLM은 느릴 수 있으므로 5분
                )
                response.raise_for_status()

                result = response.json()
                content = result.get("message", {}).get("content", "")

                # qwen3 /think 블록 제거
                content = self._strip_thinking(content)

                if content and len(content) >= 50:
                    logger.info(f"Ollama 응답 성공: {len(content)} 글자")
                    return content.strip()

                logger.warning(f"응답이 너무 짧음 ({len(content) if content else 0} 글자)")

            except requests.exceptions.ConnectionError:
                logger.error(f"Ollama 서버 연결 실패 (시도 {attempt}) - ollama serve 실행 확인 필요")
            except requests.exceptions.Timeout:
                logger.error(f"Ollama 응답 타임아웃 (시도 {attempt})")
            except requests.exceptions.RequestException as e:
                logger.error(f"API 호출 실패 (시도 {attempt}): {e}")
            except (KeyError, IndexError) as e:
                logger.error(f"응답 파싱 실패 (시도 {attempt}): {e}")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        return None

    @staticmethod
    def _strip_thinking(text: str) -> str:
        """qwen3 모델의 <think>...</think> 블록 제거"""
        import re

        return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()

    def summarize(
        self,
        market_data: str,
        market_quotes: Optional[Dict] = None,
        use_detailed: bool = False,
    ) -> Optional[str]:
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

        # 2단계: 문체 다듬기
        refined = self._refine_summary(draft)

        if market_quotes:
            return self._build_final_summary(refined, market_quotes, use_detailed)
        return refined

    def _refine_summary(self, draft: str) -> str:
        """2단계: 문체 다듬기"""
        refine_prompt = f"""아래 증권 시황 요약문의 문체를 다듬어주세요.

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

        refined = self._call_api(refine_prompt)

        if refined and len(refined) >= 100:
            logger.info(f"2단계 다듬기 완료: {len(refined)} 글자")
            return refined

        logger.warning("2단계 다듬기 실패, 원본 사용")
        return draft

    def _build_final_summary(self, analysis: str, quotes: Dict, use_detailed: bool) -> str:
        """분석 결과와 Yahoo 지수를 조합하여 최종 요약 생성 (PB 형식)"""

        def fmt_index(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            pct = q["change_pct"]
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
            sign = "+" if q["change_pct"] >= 0 else ""
            return f"{q['price']:.2f} ({sign}{q['change_pct']:.2f}%)"

        def fmt_oil(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            sign = "+" if q["change_pct"] >= 0 else ""
            return f"{q['price']:.2f}달러 ({sign}{q['change_pct']:.2f}%)"

        def fmt_vix(symbol: str) -> str:
            if symbol not in quotes:
                return "N/A"
            q = quotes[symbol]
            sign = "+" if q["change_pct"] >= 0 else ""
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
