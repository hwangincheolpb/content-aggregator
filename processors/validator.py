"""AI 교차 검증 모듈 - Gemini 요약을 다른 AI로 검증"""
import os
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class SummaryValidator:
    """요약 결과 검증 (Claude API 사용)"""

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: Anthropic API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude API 검증기 초기화 완료")
            except ImportError:
                logger.warning("anthropic 패키지 없음, 검증 비활성화")
            except Exception as e:
                logger.error(f"Claude API 초기화 실패: {e}")

    def validate(self, summary: str, yahoo_quotes: Dict) -> Tuple[bool, List[str]]:
        """
        요약 내용 검증

        Args:
            summary: Gemini가 생성한 요약
            yahoo_quotes: Yahoo Finance 원본 지수 데이터

        Returns:
            (검증 통과 여부, 발견된 문제 목록)
        """
        issues = []

        # 1. 기본 검증 (AI 없이)
        basic_issues = self._basic_validation(summary, yahoo_quotes)
        issues.extend(basic_issues)

        # 2. AI 검증 (Claude API가 있는 경우)
        if self.client:
            ai_issues = self._ai_validation(summary, yahoo_quotes)
            issues.extend(ai_issues)

        is_valid = len(issues) == 0
        return is_valid, issues

    def _basic_validation(self, summary: str, yahoo_quotes: Dict) -> List[str]:
        """기본 검증 (숫자 일치 확인)"""
        import re
        issues = []

        # 주요 지수 가격 확인
        checks = [
            ('^DJI', '다우', 500),      # 허용 오차
            ('^GSPC', 'S&P 500', 50),   # S&P 500 전체 매칭
            ('^IXIC', '나스닥', 200),
        ]

        for symbol, name, tolerance in checks:
            if symbol in yahoo_quotes:
                expected = yahoo_quotes[symbol]['price']
                # 쉼표 포함 숫자 패턴 (이름 뒤 숫자)
                # S&P 500: 6,875.62 형태 매칭
                escaped_name = re.escape(name)
                pattern = rf'{escaped_name}[:\s]*([0-9,]+\.?\d*)'
                match = re.search(pattern, summary, re.IGNORECASE)
                if match:
                    try:
                        found = float(match.group(1).replace(',', ''))
                        diff = abs(expected - found)
                        if diff > tolerance:
                            issues.append(f"{name} 지수 불일치: 예상 {expected:,.2f}, 발견 {found:,.2f}")
                    except ValueError:
                        pass

        return issues

    def _ai_validation(self, summary: str, yahoo_quotes: Dict) -> List[str]:
        """Claude API를 이용한 검증"""
        issues = []

        if not self.client:
            return issues

        # Yahoo 데이터 요약
        yahoo_summary = self._format_yahoo_data(yahoo_quotes)

        prompt = f"""다음 시황 요약의 정확성을 검증해주세요.

[실제 시장 데이터 (Yahoo Finance)]
{yahoo_summary}

[검증할 요약]
{summary}

검증 항목:
1. 지수 숫자가 실제 데이터와 일치하는지
2. 등락 방향(상승/하락)이 맞는지
3. 논리적으로 모순되는 내용이 있는지

문제가 있으면 각 문제를 한 줄씩 나열해주세요.
문제가 없으면 "검증 통과"만 출력하세요."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # 저렴한 모델 사용
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text.strip()
            logger.info(f"Claude 검증 결과: {result[:100]}...")

            if "검증 통과" not in result:
                # 문제점 추출
                for line in result.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        issues.append(f"[AI검증] {line}")

        except Exception as e:
            logger.error(f"Claude API 검증 실패: {e}")

        return issues

    def _format_yahoo_data(self, quotes: Dict) -> str:
        """Yahoo 데이터를 검증용 텍스트로 포맷"""
        lines = []

        name_map = {
            '^DJI': '다우존스',
            '^GSPC': 'S&P 500',
            '^IXIC': '나스닥',
            '^RUT': '러셀 2000',
            'CL=F': 'WTI 유가',
            'GC=F': '금',
            '^TNX': '10년물 금리',
            'DX-Y.NYB': '달러인덱스',
            'KRW=X': '원/달러',
            '^VIX': 'VIX',
        }

        for symbol, name in name_map.items():
            if symbol in quotes:
                q = quotes[symbol]
                direction = "상승" if q['change_pct'] >= 0 else "하락"
                lines.append(f"{name}: {q['price']:,.2f} ({direction} {abs(q['change_pct']):.2f}%)")

        return '\n'.join(lines)


def validate_summary(summary: str, yahoo_quotes: Dict, api_key: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    요약 검증 헬퍼 함수

    Args:
        summary: 검증할 요약
        yahoo_quotes: Yahoo 지수 데이터
        api_key: Anthropic API 키 (선택)

    Returns:
        (검증 통과 여부, 문제 목록)
    """
    validator = SummaryValidator(api_key)
    return validator.validate(summary, yahoo_quotes)
