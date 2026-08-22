# mingoon

구글(Gmail)과 네이버 메일의 읽지 않은 메일을 한 번에 확인하는 CLI 프로그램입니다. IMAP으로 각 서비스에 접속해 읽지 않은 메일 수와 최근 메일 제목/보낸사람을 보여줍니다.

## 설치

```bash
pip install -r requirements.txt
```

## 설정

1. `.env.example`을 `.env`로 복사합니다.
2. 사용할 계정의 이메일과 앱 비밀번호를 입력합니다. (구글/네이버 둘 중 하나만 설정해도 동작합니다.)

### 구글(Gmail) 앱 비밀번호 발급

1. 구글 계정에서 2단계 인증을 켭니다.
2. https://myaccount.google.com/apppasswords 에서 앱 비밀번호를 생성합니다.
3. 생성된 16자리 비밀번호를 `GOOGLE_APP_PASSWORD`에 입력합니다.

### 네이버 IMAP 설정

1. 네이버 메일 > 환경설정 > POP3/IMAP 설정에서 IMAP/SMTP 사용을 켭니다.
2. 네이버 보안설정에서 2단계 인증을 켠 뒤 애플리케이션 비밀번호를 생성합니다.
3. 생성된 비밀번호를 `NAVER_APP_PASSWORD`에 입력합니다.

## 실행

```bash
python main.py
```

계정별로 표시할 최근 메일 수를 조절하려면:

```bash
python main.py --limit 10
```

## 테스트

```bash
python -m unittest discover -s tests
```
