"""Content Summarizer using Claude API"""
import os
from typing import List, Dict
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """Summarizes collected content using Claude AI"""

    def __init__(self):
        """Initialize Claude API client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"  # Cost-effective model

    def _format_content(self, items: List[Dict]) -> str:
        """Format collected items into readable text"""
        formatted = []

        for item in items:
            source = item.get('source', 'Unknown')
            title = item.get('title', 'No title')
            link = item.get('link', '')
            summary = item.get('summary', '')
            published = item.get('published', '')

            # Source-specific formatting
            if source == 'RSS':
                feed = item.get('feed_title', 'Unknown Feed')
                formatted.append(f"[{source} - {feed}] {title}\n{link}\n{summary[:200]}\nPublished: {published}\n")
            elif source == 'Twitter':
                username = item.get('username', 'Unknown')
                formatted.append(f"[{source} - @{username}] {title}\n{link}\n{summary[:200]}\n")
            elif source == 'Reddit':
                subreddit = item.get('subreddit', 'Unknown')
                score = item.get('score', 0)
                formatted.append(f"[{source} - r/{subreddit}] {title} (↑{score})\n{link}\n{summary[:200]}\n")
            elif source == 'Telegram':
                channel = item.get('channel', 'Unknown')
                formatted.append(f"[{source} - {channel}] {title}\n{link}\n{summary[:200]}\n")
            else:
                formatted.append(f"[{source}] {title}\n{link}\n{summary[:200]}\n")

            formatted.append("-" * 80 + "\n")

        return "\n".join(formatted)

    def summarize(self, items: List[Dict], custom_prompt: str = None) -> str:
        """
        Summarize collected content using Claude AI

        Args:
            items: List of collected items from various sources
            custom_prompt: Optional custom prompt for summarization

        Returns:
            AI-generated summary
        """
        if not items:
            return "No content to summarize."

        # Format content
        content = self._format_content(items)

        # Default prompt
        if not custom_prompt:
            custom_prompt = f"""다음은 오늘 수집된 {len(items)}개의 콘텐츠입니다.
주요 트렌드와 핵심 내용을 한글로 요약해주세요.

요약 형식:
1. **주요 트렌드** (3-5개 키워드)
2. **핵심 뉴스/글** (중요도 순으로 5-10개, 각 항목마다 한 줄 요약 + 링크)
3. **기술/개발** 관련 내용이 있다면 별도 섹션으로
4. **흥미로운 토론/의견** 요약

간결하고 읽기 쉽게 작성해주세요."""

        try:
            logger.info(f"Sending {len(items)} items to Claude for summarization...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"{custom_prompt}\n\n--- 수집된 콘텐츠 ---\n\n{content}"
                    }
                ]
            )

            summary = response.content[0].text
            logger.info(f"Summary generated successfully ({len(summary)} characters)")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"요약 생성 중 오류 발생: {e}"

    def estimate_cost(self, items: List[Dict]) -> float:
        """
        Estimate API cost for summarization

        Args:
            items: List of items to summarize

        Returns:
            Estimated cost in USD
        """
        content = self._format_content(items)

        # Approximate token count (rough estimate: 1 token ≈ 4 characters)
        input_tokens = len(content) / 4
        output_tokens = 4000  # max_tokens

        # Haiku pricing (as of 2024)
        # Input: $0.25 / 1M tokens
        # Output: $1.25 / 1M tokens
        input_cost = (input_tokens / 1_000_000) * 0.25
        output_cost = (output_tokens / 1_000_000) * 1.25

        total_cost = input_cost + output_cost

        logger.info(f"Estimated cost: ${total_cost:.4f}")
        return total_cost


def test_summarizer():
    """Test function"""
    # Create sample data
    sample_items = [
        {
            'source': 'Twitter',
            'username': 'elonmusk',
            'title': 'Sample tweet about AI',
            'link': 'https://twitter.com/elonmusk/status/123',
            'summary': 'This is a sample tweet about artificial intelligence and the future.',
            'published': '2024-01-01T12:00:00',
        },
        {
            'source': 'Reddit',
            'subreddit': 'programming',
            'title': 'New Python 3.13 features',
            'link': 'https://reddit.com/r/programming/123',
            'summary': 'Discussion about new features in Python 3.13',
            'score': 150,
            'published': '2024-01-01T10:00:00',
        },
    ]

    summarizer = ContentSummarizer()

    # Estimate cost
    cost = summarizer.estimate_cost(sample_items)
    print(f"Estimated cost: ${cost:.4f}")

    # Generate summary
    summary = summarizer.summarize(sample_items)
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(summary)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_summarizer()
