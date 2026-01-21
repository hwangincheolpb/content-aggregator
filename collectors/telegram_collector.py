"""Telegram Collector Module"""
import os
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TelegramCollector:
    """Collects messages from Telegram channels"""

    def __init__(self, hours_back: int = 24):
        """
        Initialize Telegram collector

        Args:
            hours_back: How many hours back to collect messages (default: 24)
        """
        self.hours_back = hours_back
        self.cutoff_time = datetime.now() - timedelta(hours=hours_back)
        self.client = None

    async def _init_client(self):
        """Initialize Telegram client (requires user API credentials)"""
        try:
            from telethon import TelegramClient

            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            phone = os.getenv('TELEGRAM_PHONE')

            if not api_id or not api_hash:
                logger.warning("Telegram API credentials not found")
                return False

            self.client = TelegramClient('session_name', int(api_id), api_hash)
            await self.client.start(phone=phone)
            logger.info("Telegram client initialized")
            return True

        except ImportError:
            logger.error("telethon not installed. Install with: pip install telethon")
            return False
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {e}")
            return False

    async def collect_async(self, channels: List[str]) -> List[Dict]:
        """
        Collect messages from Telegram channels (async version)

        Args:
            channels: List of channel usernames or IDs

        Returns:
            List of messages with content, link, published date
        """
        if not self.client:
            initialized = await self._init_client()
            if not initialized:
                logger.error("Cannot collect without Telegram API credentials")
                return []

        messages = []

        for channel in channels:
            try:
                logger.info(f"Fetching messages from {channel}")

                # Get channel entity
                entity = await self.client.get_entity(channel)

                # Get recent messages
                async for message in self.client.iter_messages(entity, limit=100):
                    # Skip old messages
                    if message.date < self.cutoff_time.replace(tzinfo=message.date.tzinfo):
                        break

                    msg_data = {
                        'source': 'Telegram',
                        'channel': channel,
                        'title': message.message[:100] if message.message else 'No text',
                        'link': f"https://t.me/{channel}/{message.id}",
                        'summary': message.message or '',
                        'published': message.date.isoformat(),
                    }
                    messages.append(msg_data)

                logger.info(f"Collected {len([m for m in messages if m['channel'] == channel])} messages from {channel}")

            except Exception as e:
                logger.error(f"Error fetching messages from {channel}: {e}")
                continue

        return messages

    def collect(self, channels: List[str]) -> List[Dict]:
        """
        Collect messages from Telegram channels (sync wrapper)

        Args:
            channels: List of channel usernames (e.g., ['durov', 'telegram'])

        Returns:
            List of messages
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.collect_async(channels))

    def __del__(self):
        """Cleanup client on deletion"""
        if self.client:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.client.disconnect())
            except Exception:
                pass


def test_telegram_collector():
    """Test function"""
    collector = TelegramCollector(hours_back=48)

    # Example channels (public channels only)
    channels = [
        'durov',  # Pavel Durov's channel
    ]

    messages = collector.collect(channels)
    print(f"\nCollected {len(messages)} messages")

    for msg in messages[:3]:
        print(f"\n{msg['channel']}: {msg['title']}")
        print(f"Link: {msg['link']}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_telegram_collector()
