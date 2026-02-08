#!/usr/bin/env python3
"""
Content Aggregator - Main Script

Collects content from various sources (RSS, Twitter, Reddit, Telegram)
and generates AI-powered summaries.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import collectors
from collectors.rss_collector import RSSCollector
from collectors.twitter_collector import TwitterCollector
from collectors.reddit_collector import RedditCollector
from collectors.telegram_collector import TelegramCollector

# Import processor
from processors.summarizer import ContentSummarizer

# Import senders
from senders.email_sender import EmailSender
from senders.telegram_sender import TelegramSender

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('content_aggregator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file"""
    try:
        import yaml
        config_path = Path(__file__).parent / 'config' / 'sources.yaml'

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info("Configuration loaded successfully")
        return config

    except ImportError:
        logger.warning("PyYAML not installed. Using default config.")
        return get_default_config()
    except Exception as e:
        logger.error(f"Error loading config: {e}. Using default config.")
        return get_default_config()


def get_default_config():
    """Get default configuration"""
    return {
        'hours_back': 24,
        'rss_feeds': ['https://hnrss.org/newest'],
        'twitter_users': [],
        'reddit_subreddits': ['programming'],
        'telegram_channels': [],
        'notifications': {
            'email': {'enabled': True},
            'telegram': {'enabled': False},
            'save_to_file': {'enabled': True, 'path': 'data/summaries'}
        }
    }


def collect_all_content(config):
    """Collect content from all configured sources"""
    hours_back = config.get('hours_back', 24)
    all_items = []

    # RSS Feeds
    rss_feeds = config.get('rss_feeds', [])
    if rss_feeds:
        logger.info(f"Collecting from {len(rss_feeds)} RSS feeds...")
        rss_collector = RSSCollector(hours_back=hours_back)
        rss_items = rss_collector.collect(rss_feeds)
        all_items.extend(rss_items)
        logger.info(f"Collected {len(rss_items)} RSS items")

    # Twitter
    twitter_users = config.get('twitter_users', [])
    if twitter_users:
        logger.info(f"Collecting from {len(twitter_users)} Twitter users...")
        twitter_collector = TwitterCollector(hours_back=hours_back)
        twitter_items = twitter_collector.collect(twitter_users)
        all_items.extend(twitter_items)
        logger.info(f"Collected {len(twitter_items)} tweets")

    # Reddit
    reddit_subreddits = config.get('reddit_subreddits', [])
    if reddit_subreddits:
        logger.info(f"Collecting from {len(reddit_subreddits)} subreddits...")
        reddit_collector = RedditCollector(hours_back=hours_back)
        reddit_items = reddit_collector.collect(reddit_subreddits)
        all_items.extend(reddit_items)
        logger.info(f"Collected {len(reddit_items)} Reddit posts")

    # Telegram
    telegram_channels = config.get('telegram_channels', [])
    if telegram_channels:
        logger.info(f"Collecting from {len(telegram_channels)} Telegram channels...")
        try:
            telegram_collector = TelegramCollector(hours_back=hours_back)
            telegram_items = telegram_collector.collect(telegram_channels)
            all_items.extend(telegram_items)
            logger.info(f"Collected {len(telegram_items)} Telegram messages")
        except Exception as e:
            logger.error(f"Error collecting Telegram messages: {e}")

    logger.info(f"Total items collected: {len(all_items)}")
    return all_items


def save_summary_to_file(summary: str, items: list, config):
    """Save summary to file"""
    try:
        save_config = config.get('notifications', {}).get('save_to_file', {})
        if not save_config.get('enabled', True):
            return

        # Create directory
        save_path = Path(save_config.get('path', 'data/summaries'))
        save_path.mkdir(parents=True, exist_ok=True)

        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = save_path / f"summary_{timestamp}.md"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Daily Content Summary\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Items collected: {len(items)}\n\n")
            f.write("---\n\n")
            f.write(summary)

        logger.info(f"Summary saved to {summary_file}")

        # Save raw data
        data_file = save_path / f"data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        logger.info(f"Raw data saved to {data_file}")

    except Exception as e:
        logger.error(f"Error saving summary to file: {e}")


def send_notifications(summary: str, num_items: int, config):
    """Send notifications via configured channels"""
    notifications = config.get('notifications', {})

    # Email
    if notifications.get('email', {}).get('enabled', False):
        try:
            logger.info("Sending email notification...")
            email_sender = EmailSender()
            if email_sender.send_summary(summary, num_items):
                logger.info("Email sent successfully")
            else:
                logger.warning("Email sending failed")
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    # Telegram
    if notifications.get('telegram', {}).get('enabled', False):
        try:
            logger.info("Sending Telegram notification...")
            telegram_sender = TelegramSender()
            if telegram_sender.send_summary(summary, num_items):
                logger.info("Telegram message sent successfully")
            else:
                logger.warning("Telegram sending failed")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")


def main():
    """Main function"""
    logger.info("="*80)
    logger.info("Content Aggregator - Starting")
    logger.info("="*80)

    # Load environment variables
    load_dotenv()

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        logger.error("ANTHROPIC_API_KEY not found in environment variables!")
        logger.error("Please set it in .env file")
        sys.exit(1)

    # Load configuration
    config = load_config()

    # Collect content
    logger.info("Starting content collection...")
    items = collect_all_content(config)

    if not items:
        logger.warning("No items collected. Exiting.")
        return

    # Generate summary
    logger.info("Generating AI summary...")
    summarizer = ContentSummarizer()

    # Estimate cost
    estimated_cost = summarizer.estimate_cost(items)
    logger.info(f"Estimated API cost: ${estimated_cost:.4f}")

    # Generate summary
    summary = summarizer.summarize(items)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(summary)
    print("="*80)

    # Save to file
    save_summary_to_file(summary, items, config)

    # Send notifications
    send_notifications(summary, len(items), config)

    logger.info("Content Aggregator - Completed")
    logger.info("="*80)


if __name__ == '__main__':
    main()
