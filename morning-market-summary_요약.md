# morning-market-summary 프로젝트 요약

## 프로젝트 정보
- **레포지토리**: https://github.com/hwangincheolpb/morning-market-summary
- **목적**: 아침 시황 요약 자동화 (매일 07:00 KST)
- **OneDrive 위치**: 없음 (GitHub에만 있음)

## 기능
1. **시황 데이터 수집**:
   - 텔레그램 채널 크롤링 (BeautifulSoup)
   - Alpha Vantage API (뉴스)
   - yFinance (주요 지수)

2. **요약 생성**:
   - Gemini API로 요약

3. **전송**:
   - 텔레그램 봇으로 전송

## 현재 문제
- GitHub Actions는 작동하지만 텔레그램으로 안 옴

## 가능한 원인
1. GitHub Secrets 미설정 또는 잘못된 값
2. CHAT_ID 변환 로직 문제
3. 텔레그램 봇 권한 문제
4. 에러가 발생해도 워크플로우는 성공으로 표시

## 해결 방법
1. GitHub Secrets 확인
2. Actions 로그 확인
3. 워크플로우 수정 (필요시)
4. main.py 수정 (에러 시 실패하도록)
