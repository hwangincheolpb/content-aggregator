"""미국 마감시황 스케줄러 - 서머타임 자동 감지"""
import schedule
import time
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_us_dst() -> bool:
    """미국 서머타임 여부 확인"""
    us_eastern = ZoneInfo('America/New_York')
    now_et = datetime.now(us_eastern)
    # UTC offset이 -4면 서머타임, -5면 동절기
    return now_et.utcoffset().total_seconds() == -4 * 3600


def get_send_time() -> str:
    """
    미국 증시 마감 30분 후 한국 시간 반환
    - 정규 마감: ET 16:00
    - 서머타임(3~11월): KST 05:30
    - 동절기(11~3월): KST 06:30
    """
    if is_us_dst():
        return "05:30"
    else:
        return "06:30"


def run_market_summary():
    """main_market.py 실행"""
    try:
        logger.info("=" * 50)
        logger.info("미국 마감시황 자동 실행 시작")
        logger.info("=" * 50)

        result = subprocess.run(
            [sys.executable, "main_market.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )

        if result.returncode == 0:
            logger.info("실행 완료")
            # 출력 일부 표시
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-10:]:  # 마지막 10줄
                logger.info(line)
        else:
            logger.error(f"실행 실패: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("타임아웃 (5분 초과)")
    except Exception as e:
        logger.error(f"실행 중 오류: {e}")


def update_schedule():
    """서머타임 변경 시 스케줄 업데이트"""
    schedule.clear()
    send_time = get_send_time()
    schedule.every().day.at(send_time).do(run_market_summary)
    logger.info(f"스케줄 설정: 매일 {send_time} (서머타임: {is_us_dst()})")


def main():
    """스케줄러 메인"""
    logger.info("=" * 50)
    logger.info("미국 마감시황 스케줄러 시작")
    logger.info("=" * 50)

    # 초기 스케줄 설정
    update_schedule()

    # 매일 자정에 스케줄 업데이트 (서머타임 전환 대응)
    schedule.every().day.at("00:01").do(update_schedule)

    logger.info("스케줄러 대기 중... (Ctrl+C로 종료)")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == '__main__':
    main()
