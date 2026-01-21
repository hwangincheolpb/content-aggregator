"""Briefing.com 마감시황 수집 모듈"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BriefingCollector:
    """Briefing.com에서 미국 마감시황 수집"""

    def __init__(self, market_wrap_url: Optional[str] = None):
        """
        초기화

        Args:
            market_wrap_url: Briefing.com 마감시황 페이지 URL
        """
        # 기본 URL (Briefing.com의 마감시황 페이지)
        self.base_url = market_wrap_url or "https://www.briefing.com/stock-market-update"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def get_market_wrap(self) -> Optional[str]:
        """
        Briefing.com에서 마감시황 가져오기

        Returns:
            마감시황 텍스트 또는 None (실패 시)
        """
        try:
            logger.info(f"Briefing.com 시황 수집 시작: {self.base_url}")

            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 시황 내용이 담긴 요소 찾기
            # Briefing.com 구조에 따라 선택자 조정 필요
            content = self._extract_content(soup)

            if content:
                logger.info(f"Briefing.com 시황 수집 성공: {len(content)} 글자")
                return content
            else:
                logger.warning("Briefing.com에서 시황 내용을 찾을 수 없음")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Briefing.com 요청 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"Briefing.com 시황 수집 중 오류: {e}")
            return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        HTML에서 시황 내용 추출

        Args:
            soup: BeautifulSoup 객체

        Returns:
            시황 텍스트 또는 None
        """
        # 여러 선택자 시도 (사이트 구조에 따라 조정 필요)
        selectors = [
            # 일반적인 기사 본문 선택자
            ('article', {}),
            ('div', {'class': 'article-content'}),
            ('div', {'class': 'story-content'}),
            ('div', {'class': 'market-update'}),
            ('div', {'class': 'content'}),
            ('div', {'id': 'article-body'}),
            # Briefing.com 특화 선택자 (실제 구조 확인 필요)
            ('div', {'class': 'briefing-content'}),
            ('div', {'class': 'market-wrap'}),
        ]

        for tag, attrs in selectors:
            element = soup.find(tag, attrs) if attrs else soup.find(tag)
            if element:
                text = element.get_text(separator='\n', strip=True)
                # 최소 글자수 확인 (의미있는 내용인지)
                if len(text) > 200:
                    return self._clean_text(text)

        # 모든 선택자 실패 시, 전체 body에서 주요 텍스트 추출 시도
        body = soup.find('body')
        if body:
            # 불필요한 요소 제거
            for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()

            text = body.get_text(separator='\n', strip=True)
            if len(text) > 200:
                return self._clean_text(text[:10000])  # 최대 길이 제한

        return None

    def _clean_text(self, text: str) -> str:
        """
        텍스트 정리

        Args:
            text: 원본 텍스트

        Returns:
            정리된 텍스트
        """
        # 연속된 빈 줄 제거
        lines = text.split('\n')
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        return '\n'.join(cleaned_lines)


def test_briefing_collector():
    """테스트 함수"""
    logging.basicConfig(level=logging.INFO)

    collector = BriefingCollector()
    content = collector.get_market_wrap()

    if content:
        print("=" * 50)
        print("수집된 시황:")
        print("=" * 50)
        print(content[:2000] + "..." if len(content) > 2000 else content)
    else:
        print("시황 수집 실패")


if __name__ == '__main__':
    test_briefing_collector()
