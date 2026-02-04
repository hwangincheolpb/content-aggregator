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
from typing import Optional, List, Dict, Tuple

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
            'LLM_PROVIDER', 'LLM_FALLBACK',
            'DEEPSEEK_API_KEY', 'OPENROUTER_API_KEY', 'OPENROUTER_MODEL',
            'GEMINI_API_KEY', 'GEMINI_MODEL',
            'TELEGRAM_BOT_TOKEN', 'TELEGRAM_SEND_TO_CHAT_ID',
            'TELEGRAM_CHANNEL_USERNAME', 'BRIEFING_MARKET_WRAP_URL',
            'USE_DETAILED_FORMAT', 'LOG_LEVEL'
        ]
        for var in config_vars:
            if hasattr(config_module, var):
                settings[var] = getattr(config_module, var)
        logger.info("config.py에서 설정 로드됨")
    except ImportError:
        logger.info("config.py 없음, 환경변수 사용")

    # 환경변수로 덮어쓰기 (우선)
    env_mappings = {
        'LLM_PROVIDER': 'LLM_PROVIDER',
        'LLM_FALLBACK': 'LLM_FALLBACK',
        'DEEPSEEK_API_KEY': 'DEEPSEEK_API_KEY',
        'OPENROUTER_API_KEY': 'OPENROUTER_API_KEY',
        'OPENROUTER_MODEL': 'OPENROUTER_MODEL',
        'GEMINI_API_KEY': 'GEMINI_API_KEY',
        'TELEGRAM_BOT_TOKEN': 'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_SEND_TO_CHAT_ID': 'TELEGRAM_SEND_TO_CHAT_ID',
        'TELEGRAM_CHANNEL_USERNAME': 'TELEGRAM_CHANNEL_USERNAME',
        'BRIEFING_MARKET_WRAP_URL': 'BRIEFING_MARKET_WRAP_URL',
    }

    for config_key, env_key in env_mappings.items():
        env_value = os.getenv(env_key)
        if env_value:
            if config_key == 'TELEGRAM_SEND_TO_CHAT_ID':
                try:
                    settings[config_key] = int(env_value)
                except ValueError:
                    settings[config_key] = env_value
            else:
                settings[config_key] = env_value

    # 기본값 설정
    settings.setdefault('LLM_PROVIDER', 'deepseek')
    settings.setdefault('LLM_FALLBACK', 'openrouter')
    settings.setdefault('OPENROUTER_MODEL', 'mistralai/mistral-small')
    settings.setdefault('USE_DETAILED_FORMAT', False)
    settings.setdefault('GEMINI_MODEL', 'gemini-1.5-flash')
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
    # 텔레그램 필수
    telegram_required = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_SEND_TO_CHAT_ID']
    missing = [key for key in telegram_required if not config.get(key)]

    if missing:
        logger.error(f"텔레그램 설정 누락: {', '.join(missing)}")
        return False

    # LLM API 키 중 하나는 있어야 함
    llm_keys = {
        'DEEPSEEK_API_KEY': 'YOUR_DEEPSEEK_API_KEY',
        'OPENROUTER_API_KEY': 'YOUR_OPENROUTER_API_KEY',
        'GEMINI_API_KEY': 'YOUR_GEMINI_API_KEY'
    }

    has_valid_llm = False
    for key, placeholder in llm_keys.items():
        value = config.get(key)
        if value and value != placeholder:
            has_valid_llm = True
            logger.info(f"LLM API 키 확인됨: {key}")
            break

    if not has_valid_llm:
        logger.error("LLM API 키가 하나도 설정되지 않음 (DEEPSEEK/OPENROUTER/GEMINI 중 하나 필요)")
        return False

    return True


def collect_market_data(config: dict) -> Tuple[Optional[str], Optional[Dict]]:
    """
    시황 데이터 수집

    Args:
        config: 설정 딕셔너리

    Returns:
        (수집된 시황 데이터 문자열, Yahoo 지수 딕셔너리)
    """
    from collectors.telegram_channel_collector import TelegramChannelCollector
    from collectors.yahoo_market_collector import YahooMarketCollector

    collected_data = []
    sources = []
    yahoo_quotes = None

    # 1. Yahoo Finance 실시간 지표 수집
    try:
        logger.info("Yahoo Finance 시장 데이터 수집 시작...")
        collector = YahooMarketCollector()
        yahoo_quotes = collector.get_all_quotes()  # 지수 데이터 별도 저장
        yahoo_data = collector.get_market_summary()

        if yahoo_data:
            collected_data.append(yahoo_data)
            collected_data.append("\n\n")
            sources.append("Yahoo Finance")
            logger.info(f"Yahoo Finance 수집 성공: {len(yahoo_quotes)}개 지표")
        else:
            logger.warning("Yahoo Finance 수집 실패")
    except Exception as e:
        logger.error(f"Yahoo Finance 수집 중 오류: {e}")

    # 2. 텔레그램 채널 수집 (시황 관련 메시지)
    channel_username = config.get('TELEGRAM_CHANNEL_USERNAME')
    if channel_username:
        try:
            logger.info(f"텔레그램 채널 수집 시작: {channel_username}")
            collector = TelegramChannelCollector(channel_username)

            # 미국 시황 메시지만 필터링하여 수집
            telegram_messages = collector.get_us_market_messages()

            if telegram_messages:
                collected_data.append(f"=== 텔레그램 채널 (@{channel_username}) ===\n")
                for i, msg in enumerate(telegram_messages[:5], 1):  # 최대 5개
                    collected_data.append(f"\n[메시지 {i}]\n{msg}\n")
                collected_data.append("\n")
                sources.append(f"Telegram @{channel_username}")
                total_len = sum(len(m) for m in telegram_messages[:5])
                logger.info(f"텔레그램 채널 수집 성공: {len(telegram_messages)}개 메시지, {total_len} 글자")
            else:
                logger.warning("텔레그램 채널 수집 실패 또는 데이터 없음")
        except Exception as e:
            logger.error(f"텔레그램 채널 수집 중 오류: {e}")

    if not collected_data:
        logger.error("수집된 시황 데이터가 없습니다")
        return None, None

    combined_data = ''.join(collected_data)
    logger.info(f"총 {len(combined_data)} 글자 수집됨 (소스: {', '.join(sources)})")

    return combined_data, yahoo_quotes


def get_summarizer(provider: str, config: dict):
    """LLM 프로바이더별 summarizer 인스턴스 반환"""
    provider = provider.lower()

    if provider == 'deepseek':
        from processors.deepseek_summarizer import DeepSeekMarketSummarizer
        api_key = config.get('DEEPSEEK_API_KEY')
        if not api_key or api_key == 'YOUR_DEEPSEEK_API_KEY':
            return None
        return DeepSeekMarketSummarizer(api_key=api_key)

    elif provider == 'openrouter':
        from processors.deepseek_summarizer import OpenRouterMarketSummarizer
        api_key = config.get('OPENROUTER_API_KEY')
        if not api_key or api_key == 'YOUR_OPENROUTER_API_KEY':
            return None
        model = config.get('OPENROUTER_MODEL', 'mistralai/mistral-small')
        return OpenRouterMarketSummarizer(api_key=api_key, model_name=model)

    elif provider == 'gemini':
        from processors.gemini_summarizer import GeminiSummarizer
        api_key = config.get('GEMINI_API_KEY')
        if not api_key or api_key == 'YOUR_GEMINI_API_KEY':
            return None
        model = config.get('GEMINI_MODEL', 'gemini-1.5-flash')
        return GeminiSummarizer(api_key=api_key, model_name=model)

    return None


def summarize_market_data(market_data: str, yahoo_quotes: Optional[Dict], config: dict) -> Optional[str]:
    """
    LLM API로 시황 요약 (자동 fallback 지원)

    Args:
        market_data: 수집된 시황 데이터
        yahoo_quotes: Yahoo Finance 지수 데이터
        config: 설정 딕셔너리

    Returns:
        요약된 텍스트
    """
    main_provider = config.get('LLM_PROVIDER', 'deepseek')
    fallback_provider = config.get('LLM_FALLBACK', 'openrouter')
    use_detailed = config.get('USE_DETAILED_FORMAT', False)

    # 시도할 프로바이더 목록
    providers_to_try = [main_provider]
    if fallback_provider and fallback_provider != main_provider:
        providers_to_try.append(fallback_provider)

    for provider in providers_to_try:
        try:
            logger.info(f"{provider} API 요약 시작...")
            summarizer = get_summarizer(provider, config)

            if not summarizer:
                logger.warning(f"{provider} API 키가 설정되지 않음, 건너뜀")
                continue

            summary = summarizer.summarize(market_data, market_quotes=yahoo_quotes, use_detailed=use_detailed)

            if summary:
                logger.info(f"요약 생성 성공 ({provider}): {len(summary)} 글자")
                return summary
            else:
                logger.warning(f"{provider} 요약 실패, 다음 프로바이더 시도")

        except Exception as e:
            logger.error(f"{provider} 요약 중 오류: {e}")
            continue

    logger.error("모든 LLM 프로바이더 실패")
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

        success = sender.send_market_summary(summary)

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
    market_data, yahoo_quotes = collect_market_data(config)

    if not market_data:
        logger.error("시황 데이터 수집 실패")
        print("❌ 시황 데이터 수집 실패")
        sys.exit(1)

    print(f"✅ 시황 데이터 수집 완료 ({len(market_data)} 글자)")

    # 2단계: Gemini API 요약
    print("\n🤖 2단계: Gemini API 요약 중...")
    summary = summarize_market_data(market_data, yahoo_quotes, config)

    if not summary:
        logger.error("요약 생성 실패")
        print("❌ 요약 생성 실패")
        sys.exit(1)

    print(f"✅ 요약 생성 완료 ({len(summary)} 글자)")

    # 3단계: 요약 검증
    print("\n🔍 3단계: 요약 검증 중...")
    if yahoo_quotes:
        from processors.validator import validate_summary
        is_valid, issues = validate_summary(summary, yahoo_quotes)

        if is_valid:
            print("✅ 검증 통과")
        else:
            print(f"⚠️ 검증 경고 ({len(issues)}개 문제 발견):")
            for issue in issues[:5]:  # 최대 5개만 표시
                print(f"  - {issue}")
            logger.warning(f"검증 경고: {issues}")
    else:
        print("⏭️ Yahoo 데이터 없음, 검증 생략")

    # 요약 미리보기
    print("\n" + "-" * 40)
    print("📝 요약 미리보기:")
    print("-" * 40)
    preview = summary[:500] + "..." if len(summary) > 500 else summary
    print(preview)
    print("-" * 40)

    # 4단계: 파일 저장
    save_summary_to_file(summary, market_data)

    # 5단계: 텔레그램 전송
    print("\n📤 4단계: 텔레그램 전송 중...")
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
