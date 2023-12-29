# 기능 정의
자동으로 이벤트 페이지를 방문하여 네이버 페이 포인트(폐지)를 모으는 애플리케이션

<br><br>

# 원작 소스
https://github.com/stateofai/naver-paper

<br><br>

# 주요 기능

## 사용성 측면
* 멀티 사용자 지원: 여러 명의 네이버 아이디/비밀번호를 등록해두면 각각 포인트 수집
* 클리앙, 뽐뿌 모두 지원: 두 사이트에 등록된 네이버 페이 이벤트 모두 수집
* 사용자별 방문 기록: 사용자별로 방문한 URL을 저장함. 그래서 신규 사용자를 등록해도 폐지 줍기를 놓치지 않음.
* Docker로 패키징: Docker 이미지로 만들기 때문에 파이썬 의존 패키지 및 파이썬 버전을 신경쓰지 않아도 됨.
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

<br><br>

# 네이버 로그인 관련(feat. 플루이드님)
* 2단계 인증 되어 있으신 분은 2단계 인증 회피를 위해서 애플리케이션 비번을 만드셔야 합니다.
  * [네이버 애플리케이션 비밀번호 만들기](https://help.naver.com/service/5640/contents/8584?lang=ko)
* 네이버 로그인전용 아이디는 선택사항입니다. 만드셨다면 네이버 로그인전용 아이디를 기입하시면 됩니다.
  * [네이버 로그인 전용 아이디 만들기](https://help.naver.com/service/5640/contents/10219?lang=ko)
* 네이버 보안설정에 가시면 `타지역 로그인차단 (국내 오라클인 경우)`, `해외 로그인차단 (해외 오라클인 경우)` 꺼주셔야 정상 작동합니다.

<br><br>

# FAQ
## NaverPaper 버전 업데이트 방법
현재 실행 중인 컨테이너 종료
```
docker compose down
```

기존 이미지 제거
```
docker rmi [NaverPaper 이미지 이름 입력]
```

소스 코드 다시 다운로드
```
git pull
```

다시 이미지 빌드 및 실행
```
docker compose up -d
```

<br>

## 실행 로그 수동 확인 방법
* Docker 이미지를 빌드할 때 실행한 로그는 남지 않고, 이미지가 빌드된 이후의 실행 로그부터 남습니다.
* 혹시나 로그가 제대로 남는지 테스트해보고 싶으시면 수동으로 한번 실행한 후에 `docker compose logs` 해보시기 바랍니다.

*수동 실행 방법*
```
docker exec -it [NaverPaper 컨테이너 이름 입력] bash
```

```
python get-paper.py
```

```
exit
```
 
```
docker compose logs
```