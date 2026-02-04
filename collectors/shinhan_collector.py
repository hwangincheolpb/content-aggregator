"""신한투자증권 금융상품 리스트 수집 모듈"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
from datetime import datetime
import json
import re
import time

logger = logging.getLogger(__name__)

# Selenium import
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available")


class ShinhanCollector:
    """신한투자증권 금융상품 리스트 수집"""

    URLS = {
        'fund': 'https://www.shinhansec.com/siw/wealth-management/fund/search-detail/view.do',
        'domestic_bond': 'https://www.shinhansec.com/siw/wealth-management/bond-rp/5901/view.do',
        'overseas_bond': 'https://www.shinhansec.com/siw/wealth-management/bond-rp/5902/view.do',
        'els': 'https://www.shinhansec.com/siw/wealth-management/els/585301/view.do',
    }

    def __init__(self, use_selenium: bool = True):
        self.base_url = "https://www.shinhansec.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9',
        }
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None

    def _get_driver(self):
        if not self.use_selenium:
            return None
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Selenium WebDriver 초기화 완료")
            except Exception as e:
                logger.error(f"WebDriver 초기화 실패: {e}")
                self.use_selenium = False
                return None
        return self.driver

    def _close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Selenium WebDriver 종료")
            except:
                pass

    def fetch_page(self, url: str, wait_time: int = 8) -> Optional[BeautifulSoup]:
        try:
            if self.use_selenium:
                driver = self._get_driver()
                if driver:
                    logger.info(f"페이지 로드: {url}")
                    driver.get(url)
                    time.sleep(wait_time)
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
                        )
                    except:
                        pass
                    return BeautifulSoup(driver.page_source, 'html.parser')
            else:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"페이지 가져오기 실패: {e}")
            return None

    def fetch_fund_page(self) -> Optional[BeautifulSoup]:
        """펀드 페이지 (검색 버튼 클릭 포함)"""
        try:
            driver = self._get_driver()
            if not driver:
                return None
            
            logger.info("펀드 페이지 로드 중...")
            driver.get(self.URLS['fund'])
            time.sleep(10)
            
            # 검색 버튼 클릭
            try:
                btns = driver.find_elements(By.XPATH, "//button[contains(text(), '검색')] | //a[contains(text(), '검색')]")
                for btn in btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        logger.info("검색 버튼 클릭")
                        time.sleep(8)
                        break
            except:
                pass
            
            # 더보기 버튼 클릭
            for _ in range(5):
                try:
                    more_btns = driver.find_elements(By.XPATH, "//a[contains(text(), '더보기')] | //button[contains(text(), '더보기')]")
                    clicked = False
                    for btn in more_btns:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(2)
                            clicked = True
                            break
                    if not clicked:
                        break
                except:
                    break
            
            return BeautifulSoup(driver.page_source, 'html.parser')
        except Exception as e:
            logger.error(f"펀드 페이지 로드 실패: {e}")
            return None

    def fetch_els_page(self) -> Optional[BeautifulSoup]:
        """ELS 페이지 (더보기 버튼 클릭 포함)"""
        try:
            driver = self._get_driver()
            if not driver:
                return None
            
            logger.info("ELS 페이지 로드 중...")
            driver.get(self.URLS['els'])
            time.sleep(8)
            
            # 더보기 버튼 클릭
            for _ in range(5):
                try:
                    more_btns = driver.find_elements(By.XPATH, "//a[contains(text(), '더보기')] | //button[contains(text(), '더보기')]")
                    clicked = False
                    for btn in more_btns:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(2)
                            clicked = True
                            break
                    if not clicked:
                        break
                except:
                    break
            
            return BeautifulSoup(driver.page_source, 'html.parser')
        except Exception as e:
            logger.error(f"ELS 페이지 로드 실패: {e}")
            return None

    def parse_funds(self, soup: BeautifulSoup) -> List[Dict]:
        """펀드 파싱"""
        funds = []
        
        for table in soup.find_all('table'):
            tbody = table.find('tbody')
            if not tbody:
                continue
            
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                fund = {}
                fund_name = ''
                returns = {}
                row_text = row.get_text()
                
                # 펀드명 찾기
                for cell in cells:
                    link = cell.find('a')
                    if link:
                        text = link.get_text(strip=True)
                        if len(text) > 10 and ('투자신탁' in text or '펀드' in text or '증권' in text):
                            fund_name = text
                            break
                    spans = cell.find_all('span')
                    for span in spans:
                        text = span.get_text(strip=True)
                        if len(text) > 10 and ('투자신탁' in text or '펀드' in text):
                            fund_name = text
                            break
                    if fund_name:
                        break
                
                if not fund_name:
                    continue
                
                fund['name'] = fund_name
                
                # 수익률 추출
                percentages = re.findall(r'([+-]?\d+\.?\d*)%', row_text)
                if percentages:
                    if len(percentages) >= 1:
                        returns['1M'] = percentages[0]
                    if len(percentages) >= 2:
                        returns['3M'] = percentages[1]
                    if len(percentages) >= 3:
                        returns['6M'] = percentages[2]
                    if len(percentages) >= 4:
                        returns['1Y'] = percentages[3]
                
                fund['returns'] = returns
                
                if not any(f.get('name') == fund_name for f in funds):
                    funds.append(fund)
        
        # 필터링
        exclude = ['수익률', '선취', '보수', '설정액', '운용사', '종목명', '선택', '판매']
        filtered = [f for f in funds if not any(kw in f.get('name', '') for kw in exclude)]
        
        logger.info(f"펀드 {len(filtered)}개 파싱 완료")
        return filtered[:30]

    def parse_bonds(self, soup: BeautifulSoup) -> List[Dict]:
        """채권 파싱"""
        bonds = []
        
        for table in soup.find_all('table'):
            tbody = table.find('tbody')
            if not tbody:
                continue
            
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                bond = {}
                bond_name = ''
                row_text = row.get_text()
                
                # 종목명 찾기
                for cell in cells:
                    link = cell.find('a')
                    if link:
                        text = link.get_text(strip=True)
                        if len(text) > 3 and text not in ['선택', '매수', '매도']:
                            bond_name = text
                            break
                    else:
                        text = cell.get_text(strip=True)
                        if len(text) > 5 and ('채권' in text or '국고' in text or '공사' in text or '은행' in text or '만기' in text):
                            bond_name = text
                            break
                
                if not bond_name:
                    continue
                
                # 만기일
                date_match = re.search(r'(\d{4})[.-](\d{2})[.-](\d{2})', row_text)
                if date_match:
                    bond['maturity'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                
                # 수익률
                yield_match = re.search(r'(\d+\.?\d*)%', row_text)
                if yield_match:
                    bond['yield'] = yield_match.group(1)
                
                # 신용등급
                rating_match = re.search(r'\b(AAA|AA\+|AA-|AA|A\+|A-|A|BBB\+|BBB-|BBB)\b', row_text)
                if rating_match:
                    bond['credit_rating'] = rating_match.group(1)
                
                # 투자기간
                period_match = re.search(r'(\d+년\d*일?|\d+개월)', row_text)
                if period_match:
                    bond['period'] = period_match.group(1)
                
                exclude = ['종목명', '선택', '만기일', '투자기간', '매수', '신용등급', '구분']
                if bond_name and not any(kw in bond_name for kw in exclude):
                    bond['name'] = bond_name
                    if not any(b.get('name') == bond_name for b in bonds):
                        bonds.append(bond)
        
        logger.info(f"채권 {len(bonds)}개 파싱 완료")
        return bonds[:30]

    def parse_els_elb(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """ELS/ELB 파싱"""
        els_list = []
        elb_list = []
        
        for table in soup.find_all('table'):
            tbody = table.find('tbody')
            if not tbody:
                continue
            
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                product = {}
                row_text = row.get_text()
                
                # 상품명/기초자산 찾기
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if 'KOSPI' in text or 'S&P' in text or 'EURO' in text or 'HSI' in text or 'NIKKEI' in text:
                        product['underlying'] = text
                        break
                    link = cell.find('a')
                    if link:
                        link_text = link.get_text(strip=True)
                        if len(link_text) > 3:
                            product['name'] = link_text
                
                # 수익률
                yield_match = re.search(r'(\d+\.?\d*)%', row_text)
                if yield_match:
                    product['yield'] = yield_match.group(1)
                
                # 만기
                maturity_match = re.search(r'(\d+\.?\d*)\s*년', row_text)
                if maturity_match:
                    product['maturity'] = f"{maturity_match.group(1)}년"
                
                # 유형 구분
                product['type'] = 'ELB' if '원금지급' in row_text else 'ELS'
                
                # 청약기간
                period_match = re.search(r'(\d{4}\.\d{2}\.\d{2})\s*[~-]\s*(\d{4}\.\d{2}\.\d{2})', row_text)
                if period_match:
                    product['subscription_period'] = f"{period_match.group(1)} ~ {period_match.group(2)}"
                
                if product.get('underlying') or product.get('name'):
                    if product.get('type') == 'ELB':
                        elb_list.append(product)
                    else:
                        els_list.append(product)
        
        logger.info(f"ELS {len(els_list)}개, ELB {len(elb_list)}개 파싱 완료")
        return {'els': els_list[:20], 'elb': elb_list[:20]}

    def collect_all_products(self) -> Dict:
        """모든 상품 수집"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'funds': [],
            'bonds': [],
            'overseas_bonds': [],
            'els': [],
            'elb': [],
        }
        
        try:
            # 펀드
            logger.info("펀드 데이터 수집 중...")
            fund_soup = self.fetch_fund_page()
            if fund_soup:
                data['funds'] = self.parse_funds(fund_soup)
            
            # 장외채권
            logger.info("장외채권 데이터 수집 중...")
            bond_soup = self.fetch_page(self.URLS['domestic_bond'])
            if bond_soup:
                data['bonds'] = self.parse_bonds(bond_soup)
            
            # 해외채권
            logger.info("해외채권 데이터 수집 중...")
            overseas_soup = self.fetch_page(self.URLS['overseas_bond'])
            if overseas_soup:
                data['overseas_bonds'] = self.parse_bonds(overseas_soup)
            
            # ELS/ELB
            logger.info("ELS/ELB 데이터 수집 중...")
            els_soup = self.fetch_els_page()
            if els_soup:
                els_data = self.parse_els_elb(els_soup)
                data['els'] = els_data.get('els', [])
                data['elb'] = els_data.get('elb', [])
            
        except Exception as e:
            logger.error(f"데이터 수집 오류: {e}", exc_info=True)
        
        return data

    def format_summary(self, data: Dict) -> str:
        """발송용 텍스트 포맷"""
        lines = []
        lines.append("=" * 60)
        lines.append("신한투자증권 금융상품 리스트")
        lines.append(f"수집일시: {data.get('timestamp', 'N/A')}")
        lines.append("=" * 60)
        lines.append("")

        # 펀드
        funds = data.get('funds', [])
        if funds:
            lines.append(f"📈 펀드 ({len(funds)}개)")
            for fund in funds[:15]:
                name = fund.get('name', 'N/A')
                returns = fund.get('returns', {})
                if returns:
                    return_str = ', '.join([f"{k}: {v}%" for k, v in returns.items()])
                    lines.append(f"• {name}: {return_str}")
                else:
                    lines.append(f"• {name}")
            lines.append("")

        # 장외채권
        bonds = data.get('bonds', [])
        if bonds:
            lines.append(f"💵 장외채권 ({len(bonds)}개)")
            for bond in bonds[:15]:
                name = bond.get('name', 'N/A')
                yield_val = bond.get('yield', 'N/A')
                maturity = bond.get('maturity', bond.get('period', 'N/A'))
                credit = bond.get('credit_rating', '')
                info = f"{yield_val}%"
                if maturity != 'N/A':
                    info += f" (만기: {maturity})"
                if credit:
                    info += f" [{credit}]"
                lines.append(f"• {name}: {info}")
            lines.append("")

        # 해외채권
        overseas = data.get('overseas_bonds', [])
        if overseas:
            lines.append(f"🌍 해외채권 ({len(overseas)}개)")
            for bond in overseas[:15]:
                name = bond.get('name', 'N/A')
                yield_val = bond.get('yield', 'N/A')
                maturity = bond.get('maturity', bond.get('period', 'N/A'))
                credit = bond.get('credit_rating', '')
                info = f"{yield_val}%"
                if maturity != 'N/A':
                    info += f" (만기: {maturity})"
                if credit:
                    info += f" [{credit}]"
                lines.append(f"• {name}: {info}")
            lines.append("")

        # ELS
        els = data.get('els', [])
        if els:
            lines.append(f"📊 ELS ({len(els)}개)")
            for item in els[:10]:
                name = item.get('name', item.get('underlying', 'N/A'))
                yield_val = item.get('yield', 'N/A')
                maturity = item.get('maturity', 'N/A')
                lines.append(f"• {name}: {yield_val}% / {maturity}")
            lines.append("")

        # ELB
        elb = data.get('elb', [])
        if elb:
            lines.append(f"🔗 ELB ({len(elb)}개)")
            for item in elb[:10]:
                name = item.get('name', item.get('underlying', 'N/A'))
                yield_val = item.get('yield', 'N/A')
                maturity = item.get('maturity', 'N/A')
                lines.append(f"• {name}: {yield_val}% / {maturity}")
            lines.append("")

        lines.append("-" * 40)
        lines.append("📋 요약")
        lines.append(f"• 펀드: {len(funds)}개")
        lines.append(f"• 장외채권: {len(bonds)}개")
        lines.append(f"• 해외채권: {len(overseas)}개")
        lines.append(f"• ELS: {len(els)}개")
        lines.append(f"• ELB: {len(elb)}개")
        lines.append("=" * 60)
        
        return '\n'.join(lines)

    def generate_html_report(self, data: Dict) -> str:
        """HTML 보고서"""
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>신한투자증권 금융상품</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 3px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #1e3a8a; }}
        .section {{ margin-bottom: 30px; }}
        .section-title {{ font-size: 18px; color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #1e3a8a; color: white; padding: 10px; }}
        td {{ padding: 8px; border: 1px solid #ddd; text-align: center; }}
        tr:nth-child(even) {{ background: #f9fafb; }}
        .positive {{ color: #dc2626; }}
        .summary {{ background: #eff6ff; padding: 20px; border-radius: 8px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>신한투자증권 금융상품 리스트</h1>
        <p>수집일시: {timestamp}</p>
    </div>
"""
        # 펀드
        funds = data.get('funds', [])
        if funds:
            html += """<div class="section"><h2 class="section-title">📈 펀드</h2>
            <table><tr><th>펀드명</th><th>1M</th><th>3M</th><th>6M</th><th>1Y</th></tr>"""
            for f in funds[:20]:
                r = f.get('returns', {})
                html += f"<tr><td style='text-align:left'>{f.get('name','N/A')}</td><td class='positive'>{r.get('1M','-')}%</td><td class='positive'>{r.get('3M','-')}%</td><td class='positive'>{r.get('6M','-')}%</td><td class='positive'>{r.get('1Y','-')}%</td></tr>"
            html += "</table></div>"

        # 장외채권
        bonds = data.get('bonds', [])
        if bonds:
            html += """<div class="section"><h2 class="section-title">💵 장외채권</h2>
            <table><tr><th>종목명</th><th>수익률</th><th>만기일</th><th>신용등급</th></tr>"""
            for b in bonds[:20]:
                html += f"<tr><td>{b.get('name','N/A')}</td><td class='positive'>{b.get('yield','N/A')}%</td><td>{b.get('maturity', b.get('period','N/A'))}</td><td>{b.get('credit_rating','-')}</td></tr>"
            html += "</table></div>"

        # 해외채권
        overseas = data.get('overseas_bonds', [])
        if overseas:
            html += """<div class="section"><h2 class="section-title">🌍 해외채권</h2>
            <table><tr><th>종목명</th><th>수익률</th><th>만기일</th><th>신용등급</th></tr>"""
            for b in overseas[:20]:
                html += f"<tr><td>{b.get('name','N/A')}</td><td class='positive'>{b.get('yield','N/A')}%</td><td>{b.get('maturity', b.get('period','N/A'))}</td><td>{b.get('credit_rating','-')}</td></tr>"
            html += "</table></div>"

        # ELS
        els = data.get('els', [])
        if els:
            html += """<div class="section"><h2 class="section-title">📊 ELS</h2>
            <table><tr><th>기초자산</th><th>수익률</th><th>만기</th></tr>"""
            for e in els[:15]:
                html += f"<tr><td>{e.get('name', e.get('underlying','N/A'))}</td><td class='positive'>{e.get('yield','N/A')}%</td><td>{e.get('maturity','N/A')}</td></tr>"
            html += "</table></div>"

        # 요약
        html += f"""<div class="summary"><h3>📋 요약</h3>
        <p>펀드: {len(funds)}개 / 장외채권: {len(bonds)}개 / 해외채권: {len(overseas)}개 / ELS: {len(els)}개 / ELB: {len(data.get('elb',[]))}개</p></div>
</div></body></html>"""
        return html

    def save_to_json(self, data: Dict, filepath: str = None):
        if filepath is None:
            filepath = f"shinhan_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"저장 완료: {filepath}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    collector = ShinhanCollector()
    try:
        data = collector.collect_all_products()
        print(collector.format_summary(data))
    finally:
        collector._close_driver()
