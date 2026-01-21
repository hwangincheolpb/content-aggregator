#!/usr/bin/env python3
"""
미국 마감시황 자동화 시스템

Briefing.com과 텔레그램 채널에서 시황 수집 → Gemini API 요약 → 텔레그램 전송

Usage:
    python main_market.py

환경변수 또는 config.py에서 설정 필요:
    - GEMINI_API_KEY
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_SEND_TO_CHAT_ID
    - TELEGRAM_CHANNEL_USERNAME (선택)
    - BRIEFING_MARKET_WRAP_URL (선택)
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
def setup_logging(log_level: str = "INFO"):
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('market_summary.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)


def load_config():
    """
    설정 로드 (config.py 또는 환경변수)

    Returns:
        설정 딕셔너리
    """
    settings = {}

    # config.py 파일이 있으면 로드
    try:
        import config as config_module
        config_vars = [
            'GEMINI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_SEND_TO_CHAT_ID',
            'TELEGRAM_CHANNEL_USERNAME', 'BRIEFING_MARKET_WRAP_URL',
            'USE_DETAILED_FORMAT', 'GEMINI_MODEL', 'LOG_LEVEL'
        ]
        for var in config_vars:
            if hasattr(config_module, var):
                settings[var] = getattr(config_module, var)
        logger.info("config.py에서 설정 로드됨")
    except ImportError:
        logger.info("config.py 없음, 환경변수 사용")

    # 환경변수로 덮어쓰기 (우선)
    env_mappings = {
        'GEMINI_API_KEY': 'GEMINI_API_KEY',
        'TELEGRAM_BOT_TOKEN': 'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_SEND_TO_CHAT_ID': 'TELEGRAM_SEND_TO_CHAT_ID',
        'TELEGRAM_CHANNEL_USERNAME': 'TELEGRAM_CHANNEL_USERNAME',
        'BRIEFING_MARKET_WRAP_URL': 'BRIEFING_MARKET_WRAP_URL',
    }

    for config_key, env_key in env_mappings.items():
        env_value = os.getenv(env_key)
        if env_value:
            # CHAT_ID는 숫자로 변환
            if config_key == 'TELEGRAM_SEND_TO_CHAT_ID':
                try:
                    settings[config_key] = int(env_value)
                except ValueError:
                    settings[config_key] = env_value
            else:
                settings[config_key] = env_value

    # 기본값 설정
    settings.setdefault('USE_DETAILED_FORMAT', False)
    settings.setdefault('GEMINI_MODEL', 'gemini-2.0-flash')
    settings.setdefault('LOG_LEVEL', 'INFO')

    return settings


def validate_config(config: dict) -> bool:
    """
    필수 설정 검증

    Args:
        config: 설정 딕셔너리

    Returns:
        True if valid
    """
    required = ['GEMINI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_SEND_TO_CHAT_ID']
    missing = [key for key in required if not config.get(key)]

    if missing:
        logger.error(f"필수 설정 누락: {', '.join(missing)}")
        logger.error("config.py 또는 환경변수를 확인해주세요")
        return False

    return True


def collect_market_data(config: dict) -> Optional[str]:
    """
    시황 데이터 수집

    Args:
        config: 설정 딕셔너리

    Returns:
        수집된 시황 데이터 문자열
    """
    from collectors.briefing_collector import BriefingCollector
    from collectors.telegram_channel_collector import TelegramChannelCollector

    collected_data = []
    sources = []

    # 1. Briefing.com 수집
    briefing_url = config.get('BRIEFING_MARKET_WRAP_URL')
    try:
        logger.info("Briefing.com 시황 수집 시작...")
        collector = BriefingCollector(market_wrap_url=briefing_url if briefing_url else None)
        briefing_data = collector.get_market_wrap()

        if briefing_data:
            collected_data.append("=== Briefing.com 마감시황 ===\n")
            collected_data.append(briefing_data)
            collected_data.append("\n\n")
            sources.append("Briefing.com")
            logger.info(f"Briefing.com 수집 성공: {len(briefing_data)} 글자")
        else:
            logger.warning("Briefing.com 수집 실패 또는 데이터 없음")
    except Exception as e:
        logger.error(f"Briefing.com 수집 중 오류: {e}")

    # 2. 텔레그램 채널 수집
    channel_username = config.get('TELEGRAM_CHANNEL_USERNAME')
    if channel_username:
        try:
            logger.info(f"텔레그램 채널 수집 시작: {channel_username}")
            collector = TelegramChannelCollector(channel_username)

            # 최신 메시지 수집
            telegram_data = collector.get_latest_message()

            if telegram_data:
                collected_data.append(f"=== 텔레그램 채널 (@{channel_username}) ===\n")
                collected_data.append(telegram_data)
                collected_data.append("\n\n")
                sources.append(f"Telegram @{channel_username}")
                logger.info(f"텔레그램 채널 수집 성공: {len(telegram_data)} 글자")
            else:
                logger.warning("텔레그램 채널 수집 실패 또는 데이터 없음")
        except Exception as e:
            logger.error(f"텔레그램 채널 수집 중 오류: {e}")

    if not collected_data:
        logger.error("수집된 시황 데이터가 없습니다")
        return None

    combined_data = ''.join(collected_data)
    logger.info(f"총 {len(combined_data)} 글자 수집됨 (소스: {', '.join(sources)})")

    return combined_data


def summarize_market_data(market_data: str, config: dict) -> Optional[str]:
    """
    Gemini API로 시황 요약

    Args:
        market_data: 수집된 시황 데이터
        config: 설정 딕셔너리

    Returns:
        요약된 텍스트
    """
    from processors.gemini_summarizer import GeminiSummarizer

    try:
        logger.info("Gemini API 요약 시작...")

        summarizer = GeminiSummarizer(
            api_key=config['GEMINI_API_KEY'],
            model_name=config.get('GEMINI_MODEL', 'gemini-1.5-flash')
        )

        use_detailed = config.get('USE_DETAILED_FORMAT', False)
        summary = summarizer.summarize(market_data, use_detailed=use_detailed)

        if summary:
            logger.info(f"요약 생성 성공: {len(summary)} 글자")
            return summary
        else:
            logger.error("요약 생성 실패")
            return None

    except Exception as e:
        logger.error(f"요약 생성 중 오류: {e}")
        return None


def send_to_telegram(summary: str, config: dict) -> bool:
    """
    텔레그램으로 요약 전송

    Args:
        summary: 요약된 시황
        config: 설정 딕셔너리

    Returns:
        전송 성공 여부
    """
    from senders.telegram_sender import TelegramSender

    try:
        logger.info("텔레그램 전송 시작...")

        sender = TelegramSender(
            bot_token=config['TELEGRAM_BOT_TOKEN'],
            chat_id=str(config['TELEGRAM_SEND_TO_CHAT_ID'])
        )

        # 소스 정보 생성
        sources = []
        if config.get('BRIEFING_MARKET_WRAP_URL'):
            sources.append("Briefing.com")
        if config.get('TELEGRAM_CHANNEL_USERNAME'):
            sources.append(f"@{config['TELEGRAM_CHANNEL_USERNAME']}")
        source_info = ", ".join(sources) if sources else None

        success = sender.send_market_summary(summary, source_info=source_info)

        if success:
            logger.info("텔레그램 전송 성공")
        else:
            logger.error("텔레그램 전송 실패")

        return success

    except Exception as e:
        logger.error(f"텔레그램 전송 중 오류: {e}")
        return False


def save_summary_to_file(summary: str, market_data: str):
    """
    요약 결과를 파일로 저장

    Args:
        summary: 요약된 시황
        market_data: 원본 시황 데이터
    """
    try:
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 요약 저장
        summary_file = output_dir / f"summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# 미국 마감시황 요약\n")
            f.write(f"# 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(summary)

        logger.info(f"요약 저장: {summary_file}")

        # 원본 데이터 저장
        raw_file = output_dir / f"raw_{timestamp}.txt"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(market_data)

        logger.info(f"원본 데이터 저장: {raw_file}")

    except Exception as e:
        logger.error(f"파일 저장 실패: {e}")


def main():
    """메인 함수"""
    print("=" * 60)
    print("📈 미국 마감시황 자동화 시스템")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 설정 로드
    config = load_config()

    # 로깅 설정
    setup_logging(config.get('LOG_LEVEL', 'INFO'))

    logger.info("시스템 시작")

    # 설정 검증
    if not validate_config(config):
        logger.error("설정 검증 실패")
        sys.exit(1)

    # 1단계: 시황 데이터 수집
    print("\n📊 1단계: 시황 데이터 수집 중...")
    market_data = collect_market_data(config)

    if not market_data:
        logger.error("시황 데이터 수집 실패")
        print("❌ 시황 데이터 수집 실패")
        sys.exit(1)

    print(f"✅ 시황 데이터 수집 완료 ({len(market_data)} 글자)")

    # 2단계: Gemini API 요약
    print("\n🤖 2단계: Gemini API 요약 중...")
    summary = summarize_market_data(market_data, config)

    if not summary:
        logger.error("요약 생성 실패")
        print("❌ 요약 생성 실패")
        sys.exit(1)

    print(f"✅ 요약 생성 완료 ({len(summary)} 글자)")

    # 요약 미리보기
    print("\n" + "-" * 40)
    print("📝 요약 미리보기:")
    print("-" * 40)
    preview = summary[:500] + "..." if len(summary) > 500 else summary
    print(preview)
    print("-" * 40)

    # 3단계: 파일 저장
    save_summary_to_file(summary, market_data)

    # 4단계: 텔레그램 전송
    print("\n📤 3단계: 텔레그램 전송 중...")
    success = send_to_telegram(summary, config)

    if success:
        print("✅ 텔레그램 전송 완료")
    else:
        logger.error("텔레그램 전송 실패")
        print("❌ 텔레그램 전송 실패")
        sys.exit(1)

    # 완료
    print("\n" + "=" * 60)
    print("✅ 미국 마감시황 전송 완료!")
    print("=" * 60)

    logger.info("시스템 정상 종료")


if __name__ == '__main__':
    main()
