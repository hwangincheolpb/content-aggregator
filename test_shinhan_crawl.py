#!/usr/bin/env python3
"""신한투자증권 실제 크롤링 테스트"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from collectors.shinhan_collector import ShinhanCollector
import logging

logging.basicConfig(level=logging.INFO)

# 테스트할 URL들
urls = {
    '펀드검색': 'https://www.shinhansec.com/siw/wealth-management/fund/search-detail/view.do',
    '장외채권': 'https://www.shinhansec.com/siw/wealth-management/bond-rp/5901/view.do',
    '해외채권': 'https://www.shinhansec.com/siw/wealth-management/bond-rp/5902/view.do',
}

collector = ShinhanCollector(use_selenium=True)

try:
    for name, url in urls.items():
        print(f"\n{'='*80}")
        print(f"{name} 페이지 테스트: {url}")
        print('='*80)
        
        soup = collector.fetch_page(url)
        if soup:
            # HTML 일부 저장
            with open(f'test_{name}_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup)[:50000])  # 처음 5만자만
            
            # 테이블 찾기
            tables = soup.find_all('table')
            print(f"테이블 개수: {len(tables)}")
            
            # 주요 텍스트 확인
            text = soup.get_text()[:1000]
            print(f"\n페이지 텍스트 샘플 (처음 1000자):")
            print(text)
            print("\n")
finally:
    collector._close_driver()
