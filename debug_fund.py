"""펀드 페이지 디버그"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_fund_page():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = 'https://www.shinhansec.com/siw/wealth-management/fund/search-detail/view.do'
        logger.info(f"페이지 로드: {url}")
        driver.get(url)
        time.sleep(10)
        
        # HTML 저장
        with open('data/shinhan/fund_page_initial.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("초기 HTML 저장 완료")
        
        # 검색 버튼 찾기
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        logger.info(f"버튼 개수: {len(buttons)}")
        for i, btn in enumerate(buttons):
            try:
                text = btn.text
                cls = btn.get_attribute('class')
                if text or cls:
                    logger.info(f"버튼 {i}: text='{text}', class='{cls}'")
            except:
                pass
        
        # 링크 찾기
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            try:
                text = link.text
                href = link.get_attribute('href')
                if '검색' in text or '더보기' in text:
                    logger.info(f"링크: text='{text}', href='{href}'")
            except:
                pass
        
        # 테이블 찾기
        tables = driver.find_elements(By.TAG_NAME, 'table')
        logger.info(f"테이블 개수: {len(tables)}")
        
        # tbody 찾기
        tbodies = driver.find_elements(By.TAG_NAME, 'tbody')
        logger.info(f"tbody 개수: {len(tbodies)}")
        for i, tbody in enumerate(tbodies):
            rows = tbody.find_elements(By.TAG_NAME, 'tr')
            logger.info(f"  tbody {i}: {len(rows)} rows")
        
        input("Press Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    debug_fund_page()
