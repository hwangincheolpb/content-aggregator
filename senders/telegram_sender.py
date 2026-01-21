"""Telegram Sender Module - 미국 마감시황 전송"""
import os
import asyncio
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramSender:
    """Sends market summaries via Telegram Bot"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram bot with credentials

        Args:
            bot_token: Telegram Bot Token (환경변수 대체 가능)
            chat_id: 전송할 Chat ID (환경변수 대체 가능)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_SEND_TO_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID')

        if not all([self.bot_token, self.chat_id]):
            logger.warning("Telegram bot credentials not fully configured")

    async def send_async(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message via Telegram (async)

        Args:
            message: Message to send
            parse_mode: Parse mode (Markdown, HTML, or None)

        Returns:
            True if sent successfully
        """
        if not all([self.bot_token, self.chat_id]):
            logger.error("Telegram credentials not configured")
            return False

        try:
            from telegram import Bot

            bot = Bot(token=self.bot_token)

            # Telegram has a 4096 character limit per message
            # Split long messages
            max_length = 4000
            messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]

            for msg in messages:
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=msg,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                await asyncio.sleep(0.5)  # Avoid rate limiting

            logger.info(f"Telegram message(s) sent successfully to chat {self.chat_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message via Telegram (sync wrapper)

        Args:
            message: Message to send
            parse_mode: Parse mode (Markdown, HTML, or None)

        Returns:
            True if sent successfully
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_async(message, parse_mode))

    def send_summary(self, summary: str, num_items: int = 0) -> bool:
        """
        Send daily summary via Telegram

        Args:
            summary: Summarized content
            num_items: Number of items collected

        Returns:
            True if sent successfully
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Format message
        message = f"""📰 *Daily Content Summary*
📅 {today} | 📊 {num_items} items

{summary}

---
_Automated summary by Content Aggregator_
"""

        return self.send(message, parse_mode="Markdown")

    def send_market_summary(self, summary: str, source_info: Optional[str] = None) -> bool:
        """
        미국 마감시황 요약 전송

        Args:
            summary: Gemini로 요약된 시황 내용
            source_info: 데이터 소스 정보 (선택)

        Returns:
            True if sent successfully
        """
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 시황 전용 메시지 포맷
        message = f"""📈 *미국 마감시황 요약*
📅 {today}

{summary}
"""
        if source_info:
            message += f"\n---\n📊 _소스: {source_info}_"

        # Markdown 파싱 실패 시 일반 텍스트로 재시도
        success = self.send(message, parse_mode="Markdown")
        if not success:
            logger.warning("Markdown 전송 실패, 일반 텍스트로 재시도")
            plain_message = message.replace('*', '').replace('_', '')
            success = self.send(plain_message, parse_mode=None)

        return success


def test_telegram_sender():
    """Test function"""
    sender = TelegramSender()

    test_summary = """
*주요 트렌드*
AI, Python, Web Development

*핵심 뉴스/글*
1. New AI Model Released
   [Link](https://example.com/1)

2. Python 3.13 Beta
   [Link](https://example.com/2)

*기술/개발*
- React 19 released
- TypeScript 5.0 improvements
    """

    success = sender.send_summary(test_summary, num_items=10)

    if success:
        print("Test message sent successfully!")
    else:
        print("Failed to send test message. Check your credentials.")


def test_market_summary_sender():
    """마감시황 전송 테스트"""
    sender = TelegramSender()

    test_market_summary = """**시장 요약**
미국 증시가 기술주 강세에 힘입어 상승 마감했습니다. 연준의 금리 인하 기대감이 시장을 지지했습니다.

**주요 지수**
- S&P 500: 4,850.43 (+0.52%)
- 나스닥: 15,310.97 (+0.83%)
- 다우존스: 38,001.81 (+0.35%)

**매크로 지표**
- 미국 10년물 금리: 4.12% (-3bp)
- 달러인덱스: 103.25 (-0.15%)
- WTI 유가: $75.32 (+1.2%)
- 금: $2,025.40 (+0.3%)
"""

    success = sender.send_market_summary(test_market_summary, source_info="Briefing.com, Telegram")

    if success:
        print("Market summary sent successfully!")
    else:
        print("Failed to send market summary. Check your credentials.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # test_telegram_sender()
    test_market_summary_sender()
