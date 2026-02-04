"""Yahoo Finance API를 이용한 시장 데이터 수집 모듈"""
import yfinance as yf
from typing import Optional, Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class YahooMarketCollector:
    """Yahoo Finance API로 주요 시장 지표 수집"""

    def __init__(self):
        """초기화"""
        # 수집할 지표 정의
        self.symbols = {
            # 미국 주요 지수
            '^DJI': '다우존스',
            '^GSPC': 'S&P 500',
            '^IXIC': '나스닥',
            '^RUT': '러셀 2000',
            # 원자재
            'CL=F': 'WTI 유가',
            'GC=F': '금',
            # 채권/금리
            '^TNX': '미국 10년물 금리',
            # 환율
            'DX-Y.NYB': '달러인덱스',
            'KRW=X': '원/달러',
            # 변동성
            '^VIX': 'VIX',
            # MSCI Korea
            'EWY': 'MSCI 한국',
        }

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        개별 종목 시세 조회 (history로 전일/오늘 종가 직접 계산)

        Args:
            symbol: Yahoo Finance 심볼

        Returns:
            시세 정보 딕셔너리 또는 None
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if len(hist) < 2:
                logger.warning(f"{symbol}: 데이터 부족 ({len(hist)}일)")
                return None

            # 오늘 종가 (마지막 행)
            price = hist['Close'].iloc[-1]
            # 전일 종가 (마지막에서 두번째 행)
            prev_close = hist['Close'].iloc[-2]

            # 등락률 직접 계산
            if prev_close and prev_close > 0:
                change = price - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = 0
                change_pct = 0

            # 검증: 등락률이 ±30% 초과하면 경고
            if abs(change_pct) > 30:
                logger.warning(f"{symbol}: 등락률 이상 ({change_pct:+.2f}%) - prev:{prev_close:.2f}, now:{price:.2f}")

            return {
                'symbol': symbol,
                'price': price,
                'prev_close': prev_close,
                'change': change,
                'change_pct': change_pct,
            }

        except Exception as e:
            logger.error(f"{symbol} 조회 실패: {e}")
            return None

    def get_all_quotes(self) -> Dict[str, Dict]:
        """
        모든 지표 시세 조회

        Returns:
            심볼별 시세 정보
        """
        quotes = {}

        for symbol, name in self.symbols.items():
            quote = self.get_quote(symbol)
            if quote:
                quote['name'] = name
                quotes[symbol] = quote

        logger.info(f"총 {len(quotes)}개 지표 조회 성공")
        return quotes

    def get_market_summary(self) -> Optional[str]:
        """
        시장 요약 텍스트 생성

        Returns:
            포맷된 시장 요약 문자열
        """
        quotes = self.get_all_quotes()

        if not quotes:
            logger.error("시장 데이터 조회 실패")
            return None

        lines = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines.append(f"=== Yahoo Finance 시장 데이터 ({now}) ===\n")

        # 미국 주요 지수
        lines.append("📈 미국 주요 지수")
        for symbol in ['^DJI', '^GSPC', '^IXIC', '^RUT']:
            if symbol in quotes:
                q = quotes[symbol]
                direction = "▲" if q['change_pct'] >= 0 else "▼"
                lines.append(f"• {q['name']}: {q['price']:,.2f} ({direction}{abs(q['change_pct']):.2f}%)")

        lines.append("")

        # 원자재
        lines.append("🛢️ 원자재")
        for symbol in ['CL=F', 'GC=F']:
            if symbol in quotes:
                q = quotes[symbol]
                direction = "▲" if q['change_pct'] >= 0 else "▼"
                lines.append(f"• {q['name']}: ${q['price']:,.2f} ({direction}{abs(q['change_pct']):.2f}%)")

        lines.append("")

        # 금리/환율
        lines.append("💹 금리/환율")
        for symbol in ['^TNX', 'DX-Y.NYB', 'KRW=X']:
            if symbol in quotes:
                q = quotes[symbol]
                direction = "▲" if q['change_pct'] >= 0 else "▼"
                if symbol == '^TNX':
                    lines.append(f"• {q['name']}: {q['price']:.2f}% ({direction}{abs(q['change_pct']):.2f}%)")
                elif symbol == 'KRW=X':
                    lines.append(f"• {q['name']}: {q['price']:,.2f}원 ({direction}{abs(q['change_pct']):.2f}%)")
                else:
                    lines.append(f"• {q['name']}: {q['price']:.2f} ({direction}{abs(q['change_pct']):.2f}%)")

        lines.append("")

        # VIX
        if '^VIX' in quotes:
            q = quotes['^VIX']
            direction = "▲" if q['change_pct'] >= 0 else "▼"
            lines.append(f"📊 변동성 지수")
            lines.append(f"• {q['name']}: {q['price']:.2f} ({direction}{abs(q['change_pct']):.2f}%)")

        summary = '\n'.join(lines)
        logger.info(f"시장 요약 생성 완료: {len(summary)} 글자")

        return summary


def test_yahoo_collector():
    """테스트 함수"""
    logging.basicConfig(level=logging.INFO)

    collector = YahooMarketCollector()
    summary = collector.get_market_summary()

    if summary:
        print("=" * 50)
        print("수집된 시장 데이터:")
        print("=" * 50)
        print(summary)
    else:
        print("시장 데이터 수집 실패")


if __name__ == '__main__':
    test_yahoo_collector()
