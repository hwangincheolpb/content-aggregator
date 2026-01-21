# GitHub Actions 텔레그램 전송 문제 분석

## 발견된 프로젝트

### Cursor_Claude_웹사이트 프로젝트
- **위치**: `hwangincheol\자동화\프로젝트\Cursor_Claude_웹사이트\`
- **워크플로우**: `.github\workflows\deploy.yml`
- **현재 기능**: GitHub Pages 배포만
- **텔레그램 기능**: 없음

## 텔레그램 전송이 안 되는 일반적인 원인

### 1. Secrets 미설정
- `TELEGRAM_BOT_TOKEN`이 GitHub Secrets에 없음
- `TELEGRAM_CHAT_ID`가 GitHub Secrets에 없음

### 2. 워크플로우에 텔레그램 액션 없음
- 현재 워크플로우는 배포만 하고 텔레그램 전송 단계가 없음

### 3. 텔레그램 봇 토큰/채팅 ID 오류
- 잘못된 토큰
- 잘못된 채팅 ID

### 4. 권한 문제
- 봇이 해당 채팅방에 없음
- 봇이 메시지를 보낼 권한이 없음

## 해결 방법

### 옵션 1: 기존 워크플로우에 텔레그램 알림 추가

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
          exclude-paths: |
            .git
            .github
            README.md
            deploy.ps1
            wait_and_push.ps1
            .gitignore
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
      
      # 텔레그램 알림 추가
      - name: Send Telegram notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: |
            ✅ 배포 완료!
            Repository: ${{ github.repository }}
            Branch: ${{ github.ref }}
            Commit: ${{ github.sha }}
            URL: https://hwangincheolpb.github.io/cursor-claude-website/
```

### 옵션 2: 별도 텔레그램 전송 워크플로우 생성

`.github/workflows/telegram-notify.yml` 파일 생성

## 다음 단계

1. GitHub Secrets 확인 필요:
   - `TELEGRAM_BOT_TOKEN` 설정 여부
   - `TELEGRAM_CHAT_ID` 설정 여부

2. 워크플로우 수정 필요:
   - 텔레그램 전송 단계 추가

3. 테스트 필요:
   - 푸시 후 텔레그램 메시지 확인
