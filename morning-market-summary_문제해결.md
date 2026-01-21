# morning-market-summary 텔레그램 전송 문제 해결

## 발견된 문제점

### 1. 워크플로우 config.py 생성 로직 문제
워크플로우의 CHAT_ID 변환 부분:
```python
tid=os.environ.get('TELEGRAM_SEND_TO_CHAT_ID','').strip()
val=repr(int(tid)) if (tid and tid.lstrip('-').isdigit()) else 'None'
c=c.replace('TELEGRAM_SEND_TO_CHAT_ID = None', 'TELEGRAM_SEND_TO_CHAT_ID = '+val)
```

**문제점**:
- CHAT_ID가 빈 문자열이면 `None`으로 설정됨
- 문자열이 숫자가 아니면 `None`으로 설정됨
- `None`이면 sender.py에서 전송하지 않음

### 2. 에러가 출력되지만 워크플로우는 성공
- main.py에서 발송 실패해도 계속 진행
- 워크플로우는 성공으로 표시되지만 실제로는 전송 안 됨

### 3. 설정 검증 단계가 있지만 실패해도 계속 진행
- "Check config" 단계에서 실패하면 exit(1)이지만
- 실제로는 계속 진행될 수 있음

## 해결 방법

### 방법 1: GitHub Secrets 확인 및 수정

1. **Repository → Settings → Secrets and variables → Actions** 확인:
   - `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰 (예: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
   - `TELEGRAM_SEND_TO_CHAT_ID`: 채팅 ID (숫자만, 예: `123456789`)

2. **CHAT_ID 확인 방법**:
   - 텔레그램에서 @userinfobot에게 메시지 보내기
   - 또는 봇과 대화 시작 후 `https://api.telegram.org/bot<TOKEN>/getUpdates`에서 확인

### 방법 2: 워크플로우 수정 (권장)

워크플로우의 config.py 생성 부분을 더 안정적으로 수정:

```yaml
- name: Create config from Secrets
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_SEND_TO_CHAT_ID: ${{ secrets.TELEGRAM_SEND_TO_CHAT_ID }}
  run: |
    cp config.py.example config.py
    python -c "
    import os
    with open('config.py','r',encoding='utf-8') as f: c=f.read()
    
    # Gemini API Key
    gemini_key = os.environ.get('GEMINI_API_KEY','')
    c=c.replace('YOUR_GEMINI_API_KEY', gemini_key)
    
    # Telegram Bot Token
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN','')
    c=c.replace('YOUR_BOT_TOKEN', bot_token)
    
    # Telegram Chat ID (더 안정적인 변환)
    chat_id = os.environ.get('TELEGRAM_SEND_TO_CHAT_ID','').strip()
    if chat_id and chat_id.lstrip('-').isdigit():
        chat_id_value = int(chat_id)
        c=c.replace('TELEGRAM_SEND_TO_CHAT_ID = None', f'TELEGRAM_SEND_TO_CHAT_ID = {chat_id_value}')
    else:
        print('⚠️ TELEGRAM_SEND_TO_CHAT_ID가 유효하지 않습니다:', chat_id)
        c=c.replace('TELEGRAM_SEND_TO_CHAT_ID = None', 'TELEGRAM_SEND_TO_CHAT_ID = None')
    
    with open('config.py','w',encoding='utf-8') as f: f.write(c)
    print('✅ config.py 생성 완료')
    "

- name: Check config (BOT_TOKEN / CHAT_ID 설정 여부)
  run: |
    python -c "
    import config
    bot_token = bool(getattr(config,'TELEGRAM_BOT_TOKEN',None))
    chat_id = bool(getattr(config,'TELEGRAM_SEND_TO_CHAT_ID',None))
    print('BOT_TOKEN:', '✅ 설정됨' if bot_token else '❌ 없음')
    print('CHAT_ID:', '✅ 설정됨' if chat_id else '❌ 없음')
    if not (bot_token and chat_id):
        print('❌ 텔레그램 설정이 완료되지 않았습니다.')
        exit(1)
    "
```

### 방법 3: main.py 수정 (에러 시 워크플로우 실패)

main.py에서 발송 실패 시 워크플로우도 실패하도록:

```python
# 3. 발송
print("\n[3단계] 메시지 발송 중...")
send_success = send_summary(summary, config)

if not send_success:
    print("❌ 발송 실패 - 워크플로우 종료")
    sys.exit(1)  # 워크플로우 실패로 표시
```

## 확인 방법

### 1. Actions 로그 확인
- Repository → Actions 탭
- 최근 실행 클릭
- 로그에서 다음 확인:
  - "텔레그램 전송 성공" 메시지
  - "텔레그램 전송 실패" 메시지
  - 에러 메시지

### 2. 로컬 테스트
레포지토리를 클론해서 로컬에서 테스트:
```bash
git clone https://github.com/hwangincheolpb/morning-market-summary.git
cd morning-market-summary
cp config.py.example config.py
# config.py 수정
python main.py
```

## 다음 단계

1. GitHub Secrets 확인
2. Actions 로그 확인
3. 필요시 워크플로우 수정
4. 테스트 실행
