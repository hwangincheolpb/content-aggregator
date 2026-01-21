# morning-market-summary 문제 확인 체크리스트

## 레포지토리 정보
- **URL**: https://github.com/hwangincheolpb/morning-market-summary
- **상태**: GitHub Actions는 작동하지만 텔레그램 전송 안 됨

## 확인해야 할 사항

### 1. GitHub Secrets 확인
Repository → Settings → Secrets and variables → Actions에서:
- [ ] `GEMINI_API_KEY` 설정되어 있나요?
- [ ] `TELEGRAM_BOT_TOKEN` 설정되어 있나요?
- [ ] `TELEGRAM_SEND_TO_CHAT_ID` 설정되어 있나요? (숫자여야 함)

### 2. Actions 로그 확인
Repository → Actions 탭에서:
- [ ] 최근 실행이 성공했나요?
- [ ] "텔레그램 전송 성공" 메시지가 있나요?
- [ ] "텔레그램 전송 실패" 또는 에러 메시지가 있나요?

### 3. 코드 문제 확인
- [ ] config.py 생성 로직에서 CHAT_ID 변환이 제대로 되나요?
- [ ] sender.py에서 에러가 발생하는지 확인

## 다음 단계

1. GitHub Secrets 확인
2. Actions 로그 확인
3. 문제 원인 파악 후 수정
