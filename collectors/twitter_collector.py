"""Twitter/X Collector Module using Nitter RSS"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TwitterCollector:
    """Collects tweets from Twitter/X using Nitter RSS feeds"""

    # Public Nitter instances (may change over time)
    NITTER_INSTANCES = [
        'https://nitter.poast.org',
        'https://nitter.privacydev.net',
        'https://nitter.net',
    ]

    def __init__(self, hours_back: int = 24):
        """
        Initialize Twitter collector

        Args:
            hours_back: How many hours back to collect tweets (default: 24)
        """
        self.hours_back = hours_back
        self.cutoff_time = datetime.now() - timedelta(hours=hours_back)

    def _get_working_instance(self) -> str:
        """Find a working Nitter instance"""
        import requests

        for instance in self.NITTER_INSTANCES:
            try:
                response = requests.get(instance, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Using Nitter instance: {instance}")
                    return instance
            except Exception:
                continue

        logger.warning("No working Nitter instance found, using default")
        return self.NITTER_INSTANCES[0]

    def collect(self, usernames: List[str]) -> List[Dict]:
        """
        Collect tweets from Twitter usernames

        Args:
            usernames: List of Twitter usernames (without @)

        Returns:
            List of tweets with content, link, published date
        """
        tweets = []
        nitter_instance = self._get_working_instance()

        for username in usernames:
            try:
                # Construct Nitter RSS URL
                rss_url = f"{nitter_instance}/{username}/rss"
                logger.info(f"Fetching tweets from @{username} via {rss_url}")

                feed = feedparser.parse(rss_url)

                for entry in feed.entries:
                    # Parse published date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])

                    # Skip old tweets
                    if pub_date and pub_date < self.cutoff_time:
                        continue

                    tweet = {
                        'source': 'Twitter',
                        'username': username,
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', '').replace(nitter_instance, 'https://twitter.com'),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'published': pub_date.isoformat() if pub_date else None,
                    }
                    tweets.append(tweet)

                logger.info(f"Collected {len([t for t in tweets if t['username'] == username])} tweets from @{username}")

            except Exception as e:
                logger.error(f"Error fetching tweets from @{username}: {e}")
                continue

        return tweets


def test_twitter_collector():
    """Test function"""
    collector = TwitterCollector(hours_back=48)

    # Example usernames (without @)
    usernames = [
        'elonmusk',
        'openai',
    ]

    tweets = collector.collect(usernames)
    print(f"\nCollected {len(tweets)} tweets")

    for tweet in tweets[:3]:
        print(f"\n@{tweet['username']}: {tweet['title']}")
        print(f"Link: {tweet['link']}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_twitter_collector()
