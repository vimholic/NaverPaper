# 주요 기능

## 사용성 측면
* 멀티 사용자 지원: 여러 명의 네이버 아이디/비밀번호를 등록해두면 각각 포인트 수집
* 클리앙, 뽐뿌 모두 지원: 두 사이트에 등록된 네이버 페이 이벤트 모두 수집
* 사용자별 방문 기록: 사용자별로 방문한 URL을 저장함. 그래서 신규 사용자를 등록해도 폐지 줍기를 놓치지 않음.
* Docker 이미지화: Docker 이미지로 만들기 때문에 명령어 하나만 실행하면 됨.
* 자동 스케줄러: Docker 이미지를 빌드하면 자동으로 cronjob이 등록되기 때문에 별도로 스케줄 설정이 필요 없음.
  * 현재 6시간마다 실행하도록 설정돼 있는데, `app.cron`에서 원하는 주기로 수정해주시면 됩니다.
* Telegram 알림: 포인트 수집이 완료되면 Telegram으로 알림을 보냄.
* 실행 로그: Docker에 실행 로그를 남기기 때문에 `docker compose logs`만 입력하면 폐지 수집 로그 확인 가능.
* 오래된 캠페인 자동 삭제: 등록한 날짜로부터 60일이 지난 캠페인은 자동으로 삭제함.
  * 60일을 수정하고 싶은 경우 `fetch_url.py`에서 `delete_old_urls` 함수의 `n_days_ago = current_date - timedelta(days=60)`의 숫자를 수정하면 됩니다.

## 코드 측면
* BeautifulSoup4 대신 lxml 사용
* 방문한 URL을 TXT 파일 대신 SQLite DB에 저장(향후 확장성)
* 병렬, 비동기 실행으로 속도 개선

<br><br>

# 사용법

> Oracle Cloud의 E2 Micro 서버에서만 테스트했습니다.

<br>

* [Docker 설치](https://docs.docker.com/engine/install/)

<br>

* 소스 코드를 Git으로 Clone 또는 다운로드
```
git clone https://gitea.ai-demo.duckdns.org/jihunx/NaverPaper.git
```

<br>

* 소스 코드 폴더로 이동
```
cd NaverPaper
```

<br>

* `.env.sample` 파일을 `.env`로 이름 변경

```
mv .env.sample .env
```

<br>

* `.env` 파일을 열고 `NAVER_ID`, `NAVER_PW`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`를 수정
  * 여러 명을 등록하고 싶은 경우 콤마(,)로 구분하여 순서대로 등록
  * Telegram은 한 명에게만 발송 지원합니다. 복수 개 등록하지 마세요.

```
vi .env
```

```
NAVER_ID=아이디1,아이디2
NAVER_PW=비밀번호1,비밀번호2
TELEGRAM_TOKEN=토큰
TELEGRAM_CHAT_ID=챗ID
```

<br>

* Docker 이미지 빌드 및 실행
  * 최초 실행시 네이버 폐지 줍기를 한 번 실행합니다. 
```
docker compose up -d
# 예전 버전의 Docker인 경우 docker-compose up -d
```