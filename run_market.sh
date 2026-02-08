#!/bin/bash
# Content Aggregator - 미국 마감시황 launchd 실행 래퍼
# 매일 06:30 KST 자동 실행

set -euo pipefail

PROJECT_DIR="$HOME/dev/content-aggregator"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"

# Ollama가 떠 있는지 확인 (최대 30초 대기)
for i in $(seq 1 6); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        break
    fi
    echo "$(date): Ollama 서버 대기 중... ($i/6)"
    sleep 5
done

exec "$VENV_PYTHON" "$PROJECT_DIR/main_market.py" \
    >> "$LOG_DIR/market.log" 2>&1
