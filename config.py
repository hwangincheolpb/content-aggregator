# Content Aggregator - 미국 마감시황 자동화 설정
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# LLM 설정
# ============================================================
# 메인 LLM: "ollama" (로컬, 비용 0원), "deepseek", "openrouter", "gemini"
LLM_PROVIDER = "deepseek"

# 백업 LLM (메인 실패 시 자동 전환)
LLM_FALLBACK = "ollama"

# Ollama 설정 (로컬)
OLLAMA_MODEL = "qwen3:32b"
OLLAMA_API_URL = "http://localhost:11434/api/chat"

# DeepSeek API (백업용)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = "mistralai/mistral-small"

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================================
# 텔레그램 봇 설정 (필수)
# ============================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SEND_TO_CHAT_ID = int(os.getenv("TELEGRAM_SEND_TO_CHAT_ID", "-1002524208934"))

# ============================================================
# 텔레그램 채널 수집 설정 (선택)
# ============================================================
TELEGRAM_CHANNEL_USERNAME = "shmstory"

# ============================================================
# Briefing.com 설정 (선택)
# ============================================================
BRIEFING_MARKET_WRAP_URL = ""

# ============================================================
# 요약 설정
# ============================================================
USE_DETAILED_FORMAT = False
GEMINI_MODEL = "gemini-pro"

# ============================================================
# 로깅 설정
# ============================================================
LOG_LEVEL = "INFO"
