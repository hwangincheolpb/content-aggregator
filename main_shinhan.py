#!/usr/bin/env python3
"""
신한투자증권 금융상품 리스트 수집 스크립트

정기적으로 신한투자증권 금융상품 리스트를 수집하여 저장합니다.
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

# Import collector
from collectors.shinhan_collector import ShinhanCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shinhan_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def save_data(data: dict, collector: ShinhanCollector, output_dir: str = "data/shinhan"):
    """
    수집된 데이터를 파일로 저장

    Args:
        data: 수집된 데이터
        collector: ShinhanCollector 인스턴스
        output_dir: 저장 디렉토리
    """
    try:
        # 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 저장
        json_file = output_path / f"shinhan_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON 저장 완료: {json_file}")

        # 요약 텍스트 저장
        summary = collector.format_summary(data)
        summary_file = output_path / f"shinhan_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"요약 저장 완료: {summary_file}")

        # HTML 보고서 저장
        html_report = collector.generate_html_report(data)
        html_file = output_path / f"shinhan_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        logger.info(f"HTML 보고서 저장 완료: {html_file}")

        return json_file, summary_file, html_file

    except Exception as e:
        logger.error(f"데이터 저장 실패: {e}")
        return None, None, None


def main():
    """Main function"""
    logger.info("="*80)
    logger.info("신한투자증권 금융상품 리스트 수집 시작")
    logger.info("="*80)

    # Load environment variables
    load_dotenv()

    # 수집기 생성
    collector = ShinhanCollector(use_selenium=True)
    
    try:
        # 데이터 수집
        logger.info("데이터 수집 중...")
        data = collector.collect_all_products()
        
        if not data:
            logger.error("데이터 수집 실패")
            return

        logger.info("데이터 수집 완료")

        # 요약 출력
        summary = collector.format_summary(data)
        print("\n" + "="*80)
        print("수집된 데이터 요약")
        print("="*80)
        print(summary)
        print("="*80)

        # 파일 저장
        json_file, summary_file, html_file = save_data(data, collector)
        
        if json_file:
            logger.info(f"✅ JSON 저장: {json_file}")
            logger.info(f"✅ 요약 저장: {summary_file}")
            logger.info(f"✅ HTML 보고서: {html_file}")

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
    finally:
        # Selenium 드라이버 정리
        collector._close_driver()

    logger.info("="*80)
    logger.info("신한투자증권 금융상품 리스트 수집 완료")
    logger.info("="*80)


if __name__ == '__main__':
    main()
