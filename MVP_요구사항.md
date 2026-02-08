# Content Aggregator MVP 요구사항

## 핵심 기능

### 1. 시황 수집
- **Briefing.com** 크롤링
- **텔레그램 채널** 크롤링
- 둘 다 사용

### 2. 요약 생성
- **Gemini API**로 요약
- API 키: 있음

### 3. 전송
- **텔레그램 봇**으로 전송
- 봇 토큰: 있음

### 4. 실행
- **실행 시간**: 미국 마감 후
  - 일반: 한국시간 6시
  - 서머타임: 한국시간 5시
- **실행 환경**: GitHub Actions (우선), 로컬 PC (대안)

## 기술 스택

- Python 3.11+
- BeautifulSoup4 (Briefing.com 크롤링)
- requests (텔레그램 채널 크롤링)
- Gemini API (요약)
- python-telegram-bot (전송)
- GitHub Actions (스케줄링)

## MVP 범위

### 포함
- Briefing.com 크롤링
- 텔레그램 채널 크롤링
- Gemini API 요약
- 텔레그램 전송
- GitHub Actions 워크플로우

### 제외 (나중에)
- 보유종목 모니터링
- TOP Class 고객용 기능
- 여러 고객 전송
- 개인화된 요약

## 다음 단계

클로드코드에 넘길 수 있도록 핵심만 정리 완료
