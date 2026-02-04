# Content Aggregator - 미국 마감시황 자동화 설정
# 이 파일을 config.py로 복사하고 실제 값을 입력하세요
# cp config.py.example config.py

# ============================================================
# LLM API 설정
# ============================================================
# 메인 LLM: "deepseek" (추천), "openrouter", "gemini"
LLM_PROVIDER = "deepseek"

# 백업 LLM (메인 실패 시 자동 전환)
LLM_FALLBACK = "openrouter"

# DeepSeek API (메인 추천 - 저렴하고 품질 좋음)
# https://platform.deepseek.com/ 에서 API 키 발급
DEEPSEEK_API_KEY = "sk-35fe5976002241ff944527e97b693d13"

# OpenRouter API (백업 추천 - 여러 모델 지원, 안정적)
# https://openrouter.ai/ 에서 API 키 발급
OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
OPENROUTER_MODEL = "mistralai/mistral-small"  # 저렴하고 빠름

# Gemini API (무료 티어 있지만 제한 있음)
# Google AI Studio에서 API 키 발급: https://aistudio.google.com/apikey
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# ============================================================
# 텔레그램 봇 설정 (필수)
# ============================================================
# BotFather에서 봇 생성 후 토큰 발급: https://t.me/BotFather
TELEGRAM_BOT_TOKEN = "8308897604:AAHOfcSzxuXmC2FEvA9CNspVzAGj4MoyD7E"

# 메시지를 받을 채팅 ID (개인 또는 그룹)
# @userinfobot 또는 @getidsbot 을 통해 확인 가능
TELEGRAM_SEND_TO_CHAT_ID = -1002524208934

# ============================================================
# 텔레그램 채널 수집 설정 (선택)
# ============================================================
# 시황 정보를 수집할 공개 텔레그램 채널 사용자명
# @ 없이 채널명만 입력
TELEGRAM_CHANNEL_USERNAME = "shmstory"

# ============================================================
# Briefing.com 설정 (선택)
# ============================================================
# Briefing.com 마감시황 페이지 URL
# 기본값 사용 시 빈 문자열 유지
BRIEFING_MARKET_WRAP_URL = ""

# ============================================================
# 요약 설정
# ============================================================
# True: 상세 요약 (섹터별 동향, 내일 전망 포함)
# False: 간결 요약 (핵심 정보만)
USE_DETAILED_FORMAT = False

# Gemini 모델 선택
# 권장: "gemini-1.5-flash" (빠름, 저렴)
# 대안: "gemini-1.5-pro" (더 정확, 비용 증가)
GEMINI_MODEL = "gemini-pro"

# ============================================================
# 로깅 설정
# ============================================================
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"
