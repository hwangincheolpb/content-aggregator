#!/usr/bin/env python3
"""
신한투자증권 데이터 수집 스케줄러

정기적으로 신한투자증권 금융상품 리스트를 수집합니다.
Windows Task Scheduler 또는 cron과 함께 사용할 수 있습니다.
"""
import schedule
import time
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main_shinhan import main

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shinhan_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_collection():
    """수집 작업 실행"""
    logger.info(f"스케줄된 수집 작업 시작: {datetime.now()}")
    try:
        main()
        logger.info("스케줄된 수집 작업 완료")
    except Exception as e:
        logger.error(f"스케줄된 수집 작업 실패: {e}", exc_info=True)


def setup_schedule():
    """스케줄 설정"""
    # 매일 오전 9시에 실행
    schedule.every().day.at("09:00").do(run_collection)
    
    # 매주 월요일 오전 9시에 실행 (주간 리포트용)
    schedule.every().monday.at("09:00").do(run_collection)
    
    logger.info("스케줄 설정 완료:")
    logger.info("- 매일 09:00")
    logger.info("- 매주 월요일 09:00")


def main_scheduler():
    """스케줄러 메인 함수"""
    logger.info("="*80)
    logger.info("신한투자증권 데이터 수집 스케줄러 시작")
    logger.info("="*80)
    
    setup_schedule()
    
    # 즉시 한 번 실행 (테스트용)
    logger.info("초기 수집 실행...")
    run_collection()
    
    logger.info("스케줄러 실행 중... (Ctrl+C로 종료)")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")


if __name__ == '__main__':
    # schedule 라이브러리 설치 필요: pip install schedule
    try:
        main_scheduler()
    except ImportError:
        logger.error("schedule 라이브러리가 설치되지 않았습니다.")
        logger.error("설치: pip install schedule")
        sys.exit(1)
