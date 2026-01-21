"""텔레그램 공개 채널 웹 스크래핑 모듈"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import logging
from datetime import datetime, date
import re

logger = logging.getLogger(__name__)


class TelegramChannelCollector:
    """공개 텔레그램 채널에서 시황 메시지 수집 (웹 스크래핑 방식)"""

    def __init__(self, channel_username: str):
        """
        초기화

        Args:
            channel_username: 텔레그램 채널 사용자명 (@ 제외)
        """
        # @ 기호 제거
        self.channel_username = channel_username.lstrip('@')
        self.base_url = f"https://t.me/s/{self.channel_username}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def get_latest_message(self) -> Optional[str]:
        """
        텔레그램 채널의 최신 메시지 가져오기

        Returns:
            최신 메시지 텍스트 또는 None (실패 시)
        """
        try:
            logger.info(f"텔레그램 채널 수집 시작: {self.channel_username}")

            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 메시지 요소 찾기
            messages = soup.find_all('div', class_='tgme_widget_message_text')

            if not messages:
                logger.warning(f"채널 {self.channel_username}에서 메시지를 찾을 수 없음")
                return None

            # 가장 최신 메시지 (마지막 요소)
            latest_message = messages[-1]
            text = latest_message.get_text(separator='\n', strip=True)

            if text:
                logger.info(f"텔레그램 채널 최신 메시지 수집 성공: {len(text)} 글자")
                return text
            else:
                logger.warning("빈 메시지")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"텔레그램 채널 요청 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"텔레그램 채널 수집 중 오류: {e}")
            return None

    def get_today_messages(self) -> List[str]:
        """
        오늘 날짜의 메시지들만 가져오기

        Returns:
            오늘 메시지 목록
        """
        try:
            logger.info(f"텔레그램 채널 오늘 메시지 수집 시작: {self.channel_username}")

            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 모든 메시지 위젯 찾기
            message_widgets = soup.find_all('div', class_='tgme_widget_message')

            today = date.today()
            today_messages = []

            for widget in message_widgets:
                # 날짜/시간 정보 추출
                time_element = widget.find('time', class_='time')
                if time_element and time_element.get('datetime'):
                    try:
                        msg_datetime = datetime.fromisoformat(
                            time_element['datetime'].replace('Z', '+00:00')
                        )
                        msg_date = msg_datetime.date()

                        # 오늘 메시지인지 확인
                        if msg_date == today:
                            text_element = widget.find('div', class_='tgme_widget_message_text')
                            if text_element:
                                text = text_element.get_text(separator='\n', strip=True)
                                if text:
                                    today_messages.append(text)
                    except (ValueError, TypeError):
                        continue

            logger.info(f"오늘 메시지 {len(today_messages)}개 수집됨")
            return today_messages

        except requests.exceptions.RequestException as e:
            logger.error(f"텔레그램 채널 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"텔레그램 채널 수집 중 오류: {e}")
            return []

    def get_recent_messages(self, count: int = 5) -> List[str]:
        """
        최근 N개 메시지 가져오기

        Args:
            count: 가져올 메시지 개수

        Returns:
            메시지 목록
        """
        try:
            logger.info(f"텔레그램 채널 최근 {count}개 메시지 수집 시작")

            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            messages = soup.find_all('div', class_='tgme_widget_message_text')

            if not messages:
                logger.warning(f"채널 {self.channel_username}에서 메시지를 찾을 수 없음")
                return []

            # 최근 N개 메시지 (뒤에서부터)
            recent_messages = []
            for msg in messages[-count:]:
                text = msg.get_text(separator='\n', strip=True)
                if text:
                    recent_messages.append(text)

            logger.info(f"최근 메시지 {len(recent_messages)}개 수집됨")
            return recent_messages

        except requests.exceptions.RequestException as e:
            logger.error(f"텔레그램 채널 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"텔레그램 채널 수집 중 오류: {e}")
            return []

    def get_market_summary_messages(self, keywords: Optional[List[str]] = None) -> List[str]:
        """
        시황 관련 메시지만 필터링하여 가져오기

        Args:
            keywords: 필터링할 키워드 목록 (기본: 시황 관련 키워드)

        Returns:
            시황 관련 메시지 목록
        """
        if keywords is None:
            keywords = [
                '시황', '마감', '지수', 'S&P', 'NASDAQ', '나스닥',
                '다우', 'DOW', '금리', '환율', '원자재', '유가',
                '달러', '엔화', '금값', 'VIX'
            ]

        try:
            messages = self.get_recent_messages(count=20)

            filtered = []
            for msg in messages:
                # 키워드 중 하나라도 포함되면 추가
                if any(keyword.lower() in msg.lower() for keyword in keywords):
                    filtered.append(msg)

            logger.info(f"시황 관련 메시지 {len(filtered)}개 필터링됨")
            return filtered

        except Exception as e:
            logger.error(f"메시지 필터링 중 오류: {e}")
            return []


def test_telegram_channel_collector():
    """테스트 함수"""
    logging.basicConfig(level=logging.INFO)

    # 테스트용 공개 채널 (실제 시황 채널로 변경 필요)
    channel = "test_channel"

    collector = TelegramChannelCollector(channel)

    print("=" * 50)
    print("최신 메시지:")
    print("=" * 50)
    latest = collector.get_latest_message()
    if latest:
        print(latest[:500] + "..." if len(latest) > 500 else latest)
    else:
        print("메시지 없음")

    print("\n" + "=" * 50)
    print("최근 메시지 3개:")
    print("=" * 50)
    recent = collector.get_recent_messages(count=3)
    for i, msg in enumerate(recent, 1):
        print(f"\n--- 메시지 {i} ---")
        print(msg[:300] + "..." if len(msg) > 300 else msg)


if __name__ == '__main__':
    test_telegram_channel_collector()
