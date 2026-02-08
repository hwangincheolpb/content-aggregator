# 신한투자증권 금융상품 리스트 수집기

신한투자증권의 금융상품 리스트를 자동으로 수집하여 저장하는 도구입니다.

## 기능

- 매크로 지표 수집 (한국/미국/브라질 기준금리, 국채 수익률, 환율 등)
- 글로벌 국채 정보 수집 (국고채, 미국채, 브라질국채)
- 원화 채권 정보 수집
- 펀드 정보 수집 (주식형, 채권형, 채권혼합)
- ELB/ELS 정보 수집
- 발송용 텍스트 포맷팅
- JSON 데이터 저장

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- `selenium>=4.15.0` - 동적 웹페이지 렌더링
- `webdriver-manager>=4.0.0` - Chrome 드라이버 자동 관리
- `beautifulsoup4` - HTML 파싱
- `requests` - HTTP 요청

### 2. Chrome 브라우저 설치

Selenium은 Chrome 브라우저를 사용합니다. Chrome이 설치되어 있어야 합니다.

## 사용법

### 1. 기본 사용 (수동 실행)

```bash
python main_shinhan.py
```

또는

```bash
python collectors/shinhan_collector.py
```

### 2. 스케줄러 사용 (자동 실행)

```bash
# schedule 라이브러리 설치
pip install schedule

# 스케줄러 실행
python scheduler_shinhan.py
```

스케줄러는 다음 시간에 자동으로 실행됩니다:
- 매일 오전 9시
- 매주 월요일 오전 9시

### 3. Windows Task Scheduler 설정

1. Windows 작업 스케줄러 열기
2. "기본 작업 만들기" 선택
3. 트리거 설정 (예: 매일 오전 9시)
4. 작업 설정:
   - 프로그램: `python`
   - 인수: `C:\dev\active-projects\content-aggregator\main_shinhan.py`
   - 시작 위치: `C:\dev\active-projects\content-aggregator`

## 출력 파일

수집된 데이터는 `data/shinhan/` 디렉토리에 저장됩니다:

- `shinhan_data_YYYYMMDD_HHMMSS.json` - 원본 JSON 데이터
- `shinhan_summary_YYYYMMDD_HHMMSS.txt` - 발송용 텍스트 요약

## 데이터 구조

### JSON 데이터 구조

```json
{
  "timestamp": "2026-01-23T17:46:56.644483",
  "url": "https://www.shinhansec.com/siw/wealth-management/bond-rp/590204/view.do",
  "macro_indicators": {
    "korea_rate": "2.50",
    "us_rate": "3.75",
    "brazil_rate": "15.00"
  },
  "global_bonds": [...],
  "krw_bonds": [...],
  "funds": [...],
  "elb": [...],
  "els": [...]
}
```

### 발송용 텍스트 형식

```
================================================================================
신한투자증권 금융상품 리스트
수집일시: 2026-01-23T17:46:56.644483
================================================================================

📊 매크로 지표
• 한국 기준금리: 2.50%
• 미국 기준금리: 3.75%
• 브라질 기준금리: 15.00%

🌍 글로벌 국채
• 국고채01125-3909(19-6): 4.21%
...
```

## 문제 해결

### Selenium 오류

- Chrome 브라우저가 설치되어 있는지 확인
- `webdriver-manager`가 Chrome 드라이버를 자동으로 다운로드합니다
- 네트워크 연결 확인

### 데이터가 비어있음

- 실제 웹페이지 구조가 변경되었을 수 있습니다
- `collectors/shinhan_collector.py`의 파싱 로직을 수정해야 할 수 있습니다
- 로그 파일(`shinhan_collector.log`) 확인

### 페이지 로드 실패

- 네트워크 연결 확인
- 신한투자증권 웹사이트 접근 가능 여부 확인
- 로그인 필요 여부 확인 (필요시 쿠키/세션 추가)

## 커스터마이징

### 파싱 로직 수정

`collectors/shinhan_collector.py`의 다음 메서드를 수정하여 실제 페이지 구조에 맞게 파싱 로직을 구현하세요:

- `parse_macro_indicators()` - 매크로 지표 파싱
- `parse_global_bonds()` - 글로벌 국채 파싱
- `parse_krw_bonds()` - 원화 채권 파싱
- `parse_funds()` - 펀드 파싱
- `parse_elb()` - ELB 파싱
- `parse_els()` - ELS 파싱

### 스케줄 변경

`scheduler_shinhan.py`의 `setup_schedule()` 함수를 수정하여 원하는 시간에 실행되도록 설정하세요.

## 로그

- `shinhan_collector.log` - 수집 작업 로그
- `shinhan_scheduler.log` - 스케줄러 로그

## 참고사항

- 신한투자증권 웹사이트 구조가 변경되면 파싱 로직 수정이 필요할 수 있습니다
- 로그인이 필요한 페이지인 경우 쿠키/세션 관리 추가 필요
- 과도한 요청은 IP 차단을 유발할 수 있으므로 적절한 간격을 두고 실행하세요
