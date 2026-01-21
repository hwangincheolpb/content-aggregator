# Content Aggregator MVP 최종 요구사항

## 프로젝트 목적
고객에게 아침 시황(미국) 매일 전송 자동화

## 핵심 기능 (MVP)

### 1. 시황 데이터 수집
- **Briefing.com** 크롤링 (BeautifulSoup4)
- **텔레그램 채널** 크롤링 (requests)
- 둘 다 사용

### 2. 요약 생성
- **Gemini API**로 요약
- API 키: 있음 (나중에 설정)

### 3. 텔레그램 전송
- **python-telegram-bot** 사용
- 봇 토큰: 있음 (나중에 설정)

### 4. 자동 실행
- **실행 시간**: 미국 마감 후
  - 일반: 한국시간 6시
  - 서머타임: 한국시간 5시
- **실행 환경**: GitHub Actions (우선), 로컬 PC (대안)

## 기술 스택

- **언어**: Python 3.11+
- **크롤링**: BeautifulSoup4, requests
- **요약**: Gemini API
- **전송**: python-telegram-bot
- **스케줄링**: GitHub Actions (cron)

## 파일 구조

```
content-aggregator/
├── collectors/
│   ├── briefing_collector.py    # Briefing.com 크롤링
│   └── telegram_collector.py    # 텔레그램 채널 크롤링
├── processors/
│   └── gemini_summarizer.py     # Gemini API 요약
├── senders/
│   └── telegram_sender.py       # 텔레그램 전송
├── config.py.example            # 설정 예제
├── main.py                      # 메인 스크립트
├── requirements.txt             # 패키지 목록
└── .github/workflows/
    └── daily.yml                # GitHub Actions 워크플로우
```

## 설정 필요 사항 (나중에)

- GEMINI_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_SEND_TO_CHAT_ID
- TELEGRAM_CHANNEL_USERNAME (시황 채널)

## 참고 프로젝트
- morning-market-summary: 유사한 구조, 참고 가능

## 제외 사항 (나중에)
- 보유종목 모니터링
- TOP Class 고객용 기능
- 여러 고객 전송
- 개인화된 요약
