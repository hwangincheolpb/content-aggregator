# Content Aggregator

RSS, Twitter, Reddit, Telegram 등 다양한 소스에서 콘텐츠를 자동으로 수집하고 Claude AI로 요약해주는 Python 스크립트입니다.

## 주요 기능

- **다양한 소스 통합**
  - RSS 피드 (블로그, 뉴스)
  - Twitter/X (Nitter RSS 사용)
  - Reddit (API 또는 RSS)
  - Telegram 채널

- **AI 요약**
  - Claude API로 수집된 콘텐츠를 지능적으로 요약
  - 주요 트렌드, 핵심 뉴스, 흥미로운 토론 자동 정리

- **다양한 전송 방식**
  - 이메일 (HTML 형식)
  - Telegram 메시지
  - 파일 저장 (Markdown + JSON)

## 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
cd content-aggregator
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

선택적 패키지 (YAML 설정 파일 사용 시):
```bash
pip install pyyaml
```

### 3. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 수정:

```bash
cp .env.example .env
```

`.env` 파일 편집:

```env
# 필수: Claude API 키
ANTHROPIC_API_KEY=your_claude_api_key_here

# 선택: 이메일 설정 (Gmail 예시)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECEIVER=recipient@example.com

# 선택: Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 선택: Telegram 채널 모니터링
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=your_phone_number_here

# 선택: Reddit API
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### 4. 소스 설정

`config/sources.yaml` 파일을 수정하여 원하는 소스를 설정:

```yaml
hours_back: 24  # 몇 시간 전까지 수집할지

rss_feeds:
  - https://hnrss.org/newest
  - https://www.reddit.com/r/programming/.rss

twitter_users:
  - elonmusk
  - openai

reddit_subreddits:
  - programming
  - machinelearning

telegram_channels:
  - durov

notifications:
  email:
    enabled: true
  telegram:
    enabled: false
  save_to_file:
    enabled: true
    path: data/summaries
```

## 사용 방법

### 기본 실행

```bash
python main.py
```

### 개별 모듈 테스트

각 모듈을 개별적으로 테스트할 수 있습니다:

```bash
# RSS 수집 테스트
python collectors/rss_collector.py

# Twitter 수집 테스트
python collectors/twitter_collector.py

# Reddit 수집 테스트
python collectors/reddit_collector.py

# Telegram 수집 테스트
python collectors/telegram_collector.py

# 요약 기능 테스트
python processors/summarizer.py

# 이메일 전송 테스트
python senders/email_sender.py

# Telegram 전송 테스트
python senders/telegram_sender.py
```

## 자동 실행 설정

### Windows (작업 스케줄러)

1. 작업 스케줄러 열기
2. "기본 작업 만들기" 클릭
3. 트리거: "매일" 선택 (예: 매일 오전 9시)
4. 작업: "프로그램 시작"
5. 프로그램: `python`
6. 인수: `C:\Users\spfe0\OneDrive\content-aggregator\main.py`
7. 시작 위치: `C:\Users\spfe0\OneDrive\content-aggregator`

### Linux/Mac (cron)

```bash
# crontab 편집
crontab -e

# 매일 오전 9시 실행
0 9 * * * cd /path/to/content-aggregator && python main.py
```

## API 키 발급 방법

### Claude API 키

1. [Anthropic Console](https://console.anthropic.com/) 접속
2. API Keys 메뉴에서 새 키 생성
3. `.env` 파일에 추가

### Gmail 앱 비밀번호

1. Google 계정 > 보안
2. 2단계 인증 활성화
3. "앱 비밀번호" 생성
4. `.env` 파일에 추가

### Telegram Bot

1. Telegram에서 [@BotFather](https://t.me/BotFather) 검색
2. `/newbot` 명령으로 봇 생성
3. 토큰을 `.env` 파일에 추가
4. 봇과 대화 시작
5. `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`에서 chat_id 확인

### Telegram User API (채널 모니터링용)

1. [my.telegram.org](https://my.telegram.org/) 접속
2. API development tools에서 앱 생성
3. api_id와 api_hash를 `.env` 파일에 추가

### Reddit API

1. [Reddit Apps](https://www.reddit.com/prefs/apps) 접속
2. "create app" 클릭 (script 타입 선택)
3. client_id와 client_secret을 `.env` 파일에 추가

## 비용 예상

### Claude API (Haiku 모델 기준)

- 입력: $0.25 / 1M tokens
- 출력: $1.25 / 1M tokens

**일일 예상 비용:**
- 100개 아이템 수집: $0.002-0.005/일
- 월 비용: **$0.06-0.15**

### 기타 비용

- 모든 수집 기능: **무료** (RSS, Nitter, Reddit RSS)
- 이메일 전송: **무료** (Gmail)
- Telegram: **무료**

**총 월 비용: $0.06-0.15** (Claude API만 유료)

## 프로젝트 구조

```
content-aggregator/
├── collectors/           # 콘텐츠 수집 모듈
│   ├── rss_collector.py
│   ├── twitter_collector.py
│   ├── reddit_collector.py
│   └── telegram_collector.py
├── processors/          # 처리 모듈
│   └── summarizer.py    # Claude AI 요약
├── senders/            # 전송 모듈
│   ├── email_sender.py
│   └── telegram_sender.py
├── config/             # 설정 파일
│   └── sources.yaml
├── data/              # 데이터 저장 (자동 생성)
│   └── summaries/
├── main.py           # 메인 실행 스크립트
├── requirements.txt  # Python 패키지 목록
├── .env             # 환경 변수 (생성 필요)
└── README.md        # 이 파일
```

## 트러블슈팅

### Twitter 수집이 안 됨

Nitter 인스턴스가 다운되었을 수 있습니다. `collectors/twitter_collector.py`의 `NITTER_INSTANCES` 리스트에 다른 인스턴스를 추가하세요.

최신 인스턴스 목록: [nitter.net](https://github.com/zedeus/nitter/wiki/Instances)

### Reddit 수집이 느림

Reddit API 키를 설정하면 더 빠르게 수집할 수 있습니다. API 키 없이도 RSS로 동작합니다.

### Telegram 수집이 안 됨

Telegram User API는 첫 실행 시 인증 코드를 입력해야 합니다. 터미널에서 직접 실행하여 인증을 완료하세요.

### Claude API 오류

- API 키가 올바른지 확인
- 계정에 크레딧이 있는지 확인
- 사용량이 제한을 초과하지 않았는지 확인

## 라이선스

MIT License

## 기여

이슈나 풀 리퀘스트는 언제든 환영합니다!

## 주의사항

- 수집하는 콘텐츠의 이용 약관을 확인하세요
- API 사용 제한을 준수하세요
- 개인 정보 보호에 주의하세요 (.env 파일을 공유하지 마세요)
