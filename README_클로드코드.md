# Content Aggregator - 클로드코드 구현 가이드

## 📋 프로젝트 요약

**목적**: Briefing.com과 텔레그램 채널에서 미국 마감 시황을 수집하여 Gemini API로 요약하고, 텔레그램으로 자동 전송

**실행 시간**: 미국 마감 후 (한국시간 6시/5시)

**실행 환경**: GitHub Actions (우선), 로컬 PC (대안)

---

## 🎯 핵심 기능

1. **Briefing.com 크롤링** - 마감 후 30분 이내 업데이트되는 시황 수집
2. **텔레그램 채널 크롤링** - 공개 채널에서 최신 시황 메시지 수집
3. **Gemini API 요약** - 수집된 데이터를 한국어로 간결하게 요약
4. **텔레그램 전송** - python-telegram-bot으로 전송
5. **GitHub Actions 자동화** - 매일 자동 실행

---

## 📁 파일 구조

```
content-aggregator/
├── collectors/
│   ├── __init__.py
│   ├── briefing_collector.py           # Briefing.com 크롤링 (새로 구현)
│   └── telegram_channel_collector.py   # 텔레그램 채널 크롤링
├── processors/
│   ├── __init__.py
│   └── gemini_summarizer.py            # Gemini API 요약
├── senders/
│   ├── __init__.py
│   └── telegram_sender.py             # 텔레그램 전송 (기존 코드 활용)
├── config.py.example                  # 설정 예제
├── main.py                            # 메인 스크립트
├── requirements.txt                   # 패키지 목록
└── .github/workflows/
    └── daily.yml                      # GitHub Actions 워크플로우
```

---

## 🔧 기술 스택

- Python 3.11+
- BeautifulSoup4 (Briefing.com 크롤링)
- requests (텔레그램 채널 크롤링)
- google-generativeai (Gemini API)
- python-telegram-bot v20+ (텔레그램 전송)
- GitHub Actions (스케줄링)

---

## 📚 참고 프로젝트

### morning-market-summary
- **URL**: https://github.com/hwangincheolpb/morning-market-summary
- **유사 구조**: 텔레그램 채널 크롤링, Gemini 요약, 텔레그램 전송
- **차이점**: Briefing.com 크롤링 추가 필요

### 기존 코드
- `C:\dev\active-projects\content-aggregator\senders\telegram_sender.py` 활용 가능

---

## 📖 상세 문서

- **`클로드코드_요구사항.md`**: 상세 구현 요구사항
- **`클로드코드_지시사항.md`**: 구현 지시사항
- **`구현_체크리스트.md`**: 구현 체크리스트
- **`답변_기록.md`**: 사용자 답변 기록

---

## ✅ 완료 기준

- [ ] Briefing.com에서 시황 수집 성공
- [ ] 텔레그램 채널에서 시황 수집 성공
- [ ] Gemini API로 요약 생성 성공
- [ ] 텔레그램 전송 성공
- [ ] GitHub Actions에서 자동 실행 성공

---

## 🚀 클로드코드에 넘기기

**지시사항**:
1. `클로드코드_요구사항.md` 파일을 읽고 구현 시작
2. `morning-market-summary` 프로젝트 참고하여 유사한 구조로 구현
3. Briefing.com 크롤링은 새로 구현 필요
4. 기존 `telegram_sender.py` 코드 활용 가능

**우선순위**:
1. Briefing.com 크롤링 모듈
2. 텔레그램 채널 크롤링 모듈
3. Gemini 요약 모듈
4. 텔레그램 전송 모듈
5. 메인 스크립트 통합
6. GitHub Actions 워크플로우
