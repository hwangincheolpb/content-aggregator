"""Reddit Collector Module"""
import os
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RedditCollector:
    """Collects posts from Reddit subreddits"""

    def __init__(self, hours_back: int = 24):
        """
        Initialize Reddit collector

        Args:
            hours_back: How many hours back to collect posts (default: 24)
        """
        self.hours_back = hours_back
        self.cutoff_time = datetime.now() - timedelta(hours=hours_back)
        self.reddit = None

    def _init_reddit_api(self):
        """Initialize Reddit API (if credentials available)"""
        try:
            import praw

            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'content_aggregator_bot/1.0')

            if client_id and client_secret:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("Reddit API initialized")
            else:
                logger.info("Reddit API credentials not found, will use RSS fallback")

        except ImportError:
            logger.warning("praw not installed, using RSS fallback")
        except Exception as e:
            logger.error(f"Error initializing Reddit API: {e}")

    def collect_via_rss(self, subreddits: List[str]) -> List[Dict]:
        """Collect posts using Reddit RSS feeds (no API key needed)"""
        import feedparser

        posts = []

        for subreddit in subreddits:
            try:
                rss_url = f"https://www.reddit.com/r/{subreddit}/.rss"
                logger.info(f"Fetching r/{subreddit} via RSS: {rss_url}")

                feed = feedparser.parse(rss_url)

                for entry in feed.entries:
                    # Parse published date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])

                    # Skip old posts
                    if pub_date and pub_date < self.cutoff_time:
                        continue

                    post = {
                        'source': 'Reddit',
                        'subreddit': subreddit,
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'published': pub_date.isoformat() if pub_date else None,
                    }
                    posts.append(post)

                logger.info(f"Collected {len([p for p in posts if p['subreddit'] == subreddit])} posts from r/{subreddit}")

            except Exception as e:
                logger.error(f"Error fetching r/{subreddit}: {e}")
                continue

        return posts

    def collect_via_api(self, subreddits: List[str], limit: int = 50) -> List[Dict]:
        """Collect posts using Reddit API (requires API credentials)"""
        if not self.reddit:
            self._init_reddit_api()

        if not self.reddit:
            logger.info("Falling back to RSS method")
            return self.collect_via_rss(subreddits)

        posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                for submission in subreddit.new(limit=limit):
                    created_time = datetime.fromtimestamp(submission.created_utc)

                    # Skip old posts
                    if created_time < self.cutoff_time:
                        continue

                    post = {
                        'source': 'Reddit',
                        'subreddit': subreddit_name,
                        'title': submission.title,
                        'link': f"https://reddit.com{submission.permalink}",
                        'summary': submission.selftext[:500] if submission.selftext else '',
                        'score': submission.score,
                        'num_comments': submission.num_comments,
                        'published': created_time.isoformat(),
                    }
                    posts.append(post)

                logger.info(f"Collected {len([p for p in posts if p['subreddit'] == subreddit_name])} posts from r/{subreddit_name}")

            except Exception as e:
                logger.error(f"Error fetching r/{subreddit_name}: {e}")
                continue

        return posts

    def collect(self, subreddits: List[str]) -> List[Dict]:
        """
        Collect posts from subreddits (auto-selects API or RSS)

        Args:
            subreddits: List of subreddit names (without r/)

        Returns:
            List of posts with title, link, summary, published date
        """
        # Try API first, fallback to RSS
        if os.getenv('REDDIT_CLIENT_ID'):
            return self.collect_via_api(subreddits)
        else:
            return self.collect_via_rss(subreddits)


def test_reddit_collector():
    """Test function"""
    collector = RedditCollector(hours_back=24)

    # Example subreddits
    subreddits = [
        'programming',
        'machinelearning',
    ]

    posts = collector.collect(subreddits)
    print(f"\nCollected {len(posts)} posts")

    for post in posts[:3]:
        print(f"\nr/{post['subreddit']}: {post['title']}")
        print(f"Link: {post['link']}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_reddit_collector()
