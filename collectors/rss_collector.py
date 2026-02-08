"""RSS Feed Collector Module"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RSSCollector:
    """Collects articles from RSS feeds"""

    def __init__(self, hours_back: int = 24):
        """
        Initialize RSS collector

        Args:
            hours_back: How many hours back to collect articles (default: 24)
        """
        self.hours_back = hours_back
        self.cutoff_time = datetime.now() - timedelta(hours=hours_back)

    def collect(self, feed_urls: List[str]) -> List[Dict]:
        """
        Collect articles from multiple RSS feeds

        Args:
            feed_urls: List of RSS feed URLs

        Returns:
            List of articles with title, link, summary, published date
        """
        articles = []

        for url in feed_urls:
            try:
                logger.info(f"Fetching RSS feed: {url}")
                feed = feedparser.parse(url)

                for entry in feed.entries:
                    # Parse published date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed'):
                        pub_date = datetime(*entry.updated_parsed[:6])

                    # Skip old articles
                    if pub_date and pub_date < self.cutoff_time:
                        continue

                    article = {
                        'source': 'RSS',
                        'feed_title': feed.feed.get('title', 'Unknown'),
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'published': pub_date.isoformat() if pub_date else None,
                    }
                    articles.append(article)

                logger.info(f"Collected {len(articles)} articles from {url}")

            except Exception as e:
                logger.error(f"Error fetching RSS feed {url}: {e}")
                continue

        return articles


def test_rss_collector():
    """Test function"""
    collector = RSSCollector(hours_back=48)

    # Example feeds
    feeds = [
        'https://hnrss.org/newest',  # Hacker News
        'https://www.reddit.com/r/programming/.rss',  # Reddit Programming
    ]

    articles = collector.collect(feeds)
    print(f"\nCollected {len(articles)} articles")

    for article in articles[:3]:
        print(f"\n{article['feed_title']}: {article['title']}")
        print(f"Link: {article['link']}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_rss_collector()
