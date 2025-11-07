# NaverPaper

![CI Tests](https://github.com/vimholic/NaverPaper/actions/workflows/test.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

자동으로 이벤트 페이지를 방문하여 네이버 페이 포인트(폐지)를 모으는 애플리케이션

## 목차

- [원작 소스](#원작-소스)
- [주요 기능](#주요-기능)
- [최근 개선사항](#최근-개선사항)
- [사용법](#사용법)
- [네이버 로그인 관련](#네이버-로그인-관련)
- [FAQ](#faq)

## 원작 소스

https://github.com/stateofai/naver-paper

## 주요 기능

### 사용성 측면

* **멀티 사용자 지원**: 여러 명의 네이버 아이디/비밀번호를 등록해두면 각각 포인트 수집
* **다양한 사이트 지원**: 클리앙, 뽐뿌, 다모앙에 등록된 네이버 페이 이벤트 모두 수집
* **사용자별 방문 기록**: 사용자별로 방문한 URL을 저장함. 그래서 신규 사용자를 등록해도 폐지 줍기를 놓치지 않음
* **Docker로 패키징**: Docker 이미지로 만들기 때문에 파이썬 의존 패키지 및 파이썬 버전을 신경쓰지 않아도 됨
* **자동 스케줄러**: Docker 이미지를 빌드하면 자동으로 cronjob이 등록되기 때문에 별도로 스케줄 설정이 필요 없음
  * 현재 6시간마다 실행하도록 설정돼 있는데, `app.cron`에서 원하는 주기로 수정 가능
* **Telegram 알림**: 포인트 수집이 완료되면 Telegram으로 알림을 보냄
* **실행 로그**: Docker에 실행 로그를 남기기 때문에 `docker compose logs`만 입력하면 폐지 수집 로그 확인 가능
* **오래된 캠페인 자동 삭제**: 등록한 날짜로부터 60일이 지난 캠페인은 자동으로 삭제함
  * 60일을 수정하고 싶은 경우 `fetch_url.py`에서 `delete_old_urls` 함수의 `n_days_ago = current_date - timedelta(days=60)`의 숫자를 수정

### 코드 측면

* **lxml 사용**: BeautifulSoup4 대신 lxml 사용으로 파싱 속도 개선
* **SQLite DB 저장**: 방문한 URL을 TXT 파일 대신 SQLite DB에 저장(향후 확장성)
* **병렬/비동기 실행**: 병렬, 비동기 실행으로 속도 개선
* **코드 품질 관리**: flake8, black, isort를 통한 코드 스타일 관리
* **테스트 코드**: pytest 기반 유닛 테스트 및 CI/CD 파이프라인

## 최근 개선사항

### 개발 환경 및 코드 품질

* **GitHub Actions CI/CD 파이프라인 구축**: Python 3.8~3.11 버전에서 자동 테스트 및 코드 검증
  * 자동 린트 검사 (flake8)
  * 코드 포맷팅 검사 (black, isort)
  * 코드 커버리지 측정 및 Codecov 연동
* **테스트 인프라 구축**: pytest 기반 유닛 테스트 및 비동기 테스트 지원
  * `pytest.ini` 설정 파일 추가
  * `requirements-dev.txt`로 개발 의존성 분리
* **코드 품질 개선**:
  * flake8 린트 오류 수정
  * import 순서 정리 (isort)
  * PEP 8 코딩 스타일 준수

### 기능 개선

* **환경 변수 기반 설정 관리**: `config.py`를 통한 체계적인 설정 관리
* **로깅 시스템 개선**: 통합 로깅 시스템으로 코드 중복 제거 및 로그 추적 개선
* **Cloudflare 우회 기능**: Playwright를 사용한 Cloudflare 우회 기능 추가
* **쿠키 저장 기능**: `save_cookies.py`를 통해 로컬에서 쿠키 생성 후 서버에서 사용 가능
  * 서버에서 캡챠로 인한 로그인 실패 시 로컬 PC에서 쿠키 생성 후 활용 가능

### Docker 개선

* **Ubuntu 22.04 기반 이미지**: Playwright 의존성 설치 문제 해결
* **Dockerfile 최적화**: 이미지 빌드 속도 및 안정성 개선

### 버그 수정

* pytest 사용 및 PYTHONPATH 설정으로 모듈 import 문제 해결
* requirements.txt 정리 및 불필요한 의존성 제거
* 뽐뿌, 클리앙, 다모앙 URL 수집 현행화

## 사용법

> Oracle Cloud의 E2 Micro, A1 서버, 시놀로지에서 정상 동작 확인했습니다.

### 1. Docker 설치

[Docker 설치 가이드](https://docs.docker.com/engine/install/)

### 2. 소스 코드 다운로드

```bash
git clone https://github.com/vimholic/NaverPaper.git
cd NaverPaper
```

### 3. 환경 변수 설정

`.env.sample` 파일을 `.env`로 복사하고 설정 값을 입력합니다:

```bash
mv .env.sample .env
vi .env
```

환경 변수 예시:
```bash
NAVER_ID=아이디1|아이디2
NAVER_PW=비밀번호1|비밀번호2
TELEGRAM_TOKEN=토큰1|토큰2
TELEGRAM_CHAT_ID=챗ID1|챗ID2
```

**참고사항:**
* 여러 명을 등록하고 싶은 경우 파이프(`|`)로 구분하여 순서대로 등록
* Telegram을 사용하지 않는 경우 `TELEGRAM_TOKEN` 또는 `TELEGRAM_CHAT_ID`를 공란으로 두면 됨
* 사용하는 경우 `NAVER_ID`에 입력한 사람 수만큼 쌍으로 입력해야 함

### 4. Docker 이미지 빌드 및 실행

```bash
docker compose up -d
# 예전 버전의 Docker인 경우: docker-compose up -d
```

최초 실행시 네이버 폐지 줍기를 한 번 실행합니다.

## 네이버 로그인 관련

### 2단계 인증 설정

2단계 인증을 사용 중인 경우 애플리케이션 비밀번호를 생성해야 합니다:
* [네이버 애플리케이션 비밀번호 만들기](https://help.naver.com/service/5640/contents/8584?lang=ko)

### 로그인 전용 아이디 (선택사항)

네이버 로그인 전용 아이디를 사용할 수 있습니다:
* [네이버 로그인 전용 아이디 만들기](https://help.naver.com/service/5640/contents/10219?lang=ko)

### 보안 설정

네이버 보안 설정에서 다음 항목을 비활성화해야 합니다:
* **타지역 로그인차단** (국내 서버 사용시)
* **해외 로그인차단** (해외 서버 사용시)

## FAQ

### NaverPaper 버전 업데이트 방법

1. 현재 실행 중인 컨테이너 종료
```bash
docker compose down
```

2. 기존 이미지 제거
```bash
docker rmi [NaverPaper 이미지 이름 입력]
```

3. 소스 코드 업데이트
```bash
git pull
```

4. 이미지 재빌드 및 실행
```bash
docker compose up -d
```

### 실행 시간 관련

기본적으로 한국 시간 기준 **3시, 9시, 15시, 21시** (하루 4번) 실행됩니다.

**변경 방법:**
* **방법 1**: `app.cron` 파일 수정 후 이미지 재빌드
* **방법 2**: 컨테이너 쉘 접속 후 `crontab -e` 명령어로 직접 수정

### 텔레그램 알림을 받고 싶지 않은 경우

`.env` 파일의 `TELEGRAM_CHAT_ID` 또는 `TELEGRAM_TOKEN` 중 하나라도 입력하지 않으면 알림이 발송되지 않습니다.

### 네이버 폐지 줍기를 수동으로 실행하는 방법

**대화형 실행:**
```bash
docker exec -it [NaverPaper 컨테이너 이름] bash
python get_paper.py
exit
```

**단일 명령어 실행:**
```bash
docker exec [NaverPaper 컨테이너 이름] python get_paper.py
```

### 시놀로지 컨테이너 매니저 설치시 에러 해결

**에러**: `ERROR [ 4/10] RUN apt-get update && apt-get install -y cron vim`

#### 해결 방법 1: Docker 재시작

SSH로 접속하여 Docker를 재시작합니다:

```bash
sudo service docker restart
# 또는
sudo /etc/init.d/docker restart
# 또는
sudo snap restart docker
```

참고: https://stackoverflow.com/questions/61567404/docker-temporary-failure-resolving-deb-debian-org

#### 해결 방법 2: 시놀로지 지식센터 해결 방법

시놀로지 공식 가이드를 참고하세요:
https://kb.synology.com/ko-kr/DSM/tutorial/Why_cant_I_pull_docker_images

#### 해결 방법 3: Docker Daemon에 구글 DNS 등록

`/etc/docker/daemon.json` 파일 생성 후 아래 내용 추가:

```json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

#### 해결 방법 4: vim/cron 없이 설치

vim과 cron은 폐지 수집에 필수가 아닙니다. Dockerfile에서 해당 부분을 주석 처리하고, 시놀로지 작업 스케줄러를 사용할 수 있습니다.

**Dockerfile 수정** (아래 부분 주석 처리):

```dockerfile
# RUN apt-get update \
#   && apt-get install -y cron vim
#
# COPY app.cron /etc/cron.d/app-cron
#
# RUN chmod 0644 /etc/cron.d/app-cron
#
# RUN crontab /etc/cron.d/app-cron
#
# CMD cron -f
```

**시놀로지 작업 스케줄러 설정:**

1. `생성 > 예약된 작업 > 사용자 정의 스크립트` 선택
2. 원하는 스케줄 선택
3. 사용자 정의 스크립트에 다음 입력:

```bash
docker exec [NaverPaper 컨테이너 이름] python get_paper.py
```

## 라이선스

MIT License

## 기여

이슈와 PR은 언제나 환영합니다!
