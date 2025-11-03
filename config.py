"""
설정 관리 모듈

환경 변수를 통해 애플리케이션 설정을 관리합니다.
.env 파일에서 설정을 읽어오며, 기본값을 제공합니다.

사용 예시:
    >>> from config import Config
    >>> print(Config.CAMPAIGN_RETENTION_DAYS)
    60
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """애플리케이션 설정 클래스"""

    # ==================== 네이버 계정 설정 ====================
    NAVER_IDS = os.getenv("NAVER_ID", "").split('|')
    NAVER_PWS = os.getenv("NAVER_PW", "").split('|')

    # ==================== 텔레그램 설정 ====================
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    NO_PAPER_ALARM = os.getenv("NO_PAPER_ALARM", "False") == "True"

    # ==================== 데이터 보존 기간 ====================
    # 캠페인 URL 보존 기간 (일)
    CAMPAIGN_RETENTION_DAYS = int(os.getenv("CAMPAIGN_RETENTION_DAYS", "60"))

    # 사용자 세션 보존 기간 (일)
    USER_SESSION_RETENTION_DAYS = int(os.getenv("USER_SESSION_RETENTION_DAYS", "7"))

    # ==================== 대기 시간 설정 (초) ====================
    # 페이지 로딩 후 짧은 대기 시간
    PAGE_WAIT_SHORT = int(os.getenv("PAGE_WAIT_SHORT", "3"))

    # 페이지 로딩 후 긴 대기 시간
    PAGE_WAIT_LONG = int(os.getenv("PAGE_WAIT_LONG", "5"))

    # 쿠키 저장 시 로그인 대기 시간
    LOGIN_WAIT_TIMEOUT = int(os.getenv("LOGIN_WAIT_TIMEOUT", "60"))

    # ==================== Playwright 설정 ====================
    # Playwright 네트워크 대기 타임아웃 (밀리초)
    PLAYWRIGHT_NETWORK_TIMEOUT = int(os.getenv("PLAYWRIGHT_NETWORK_TIMEOUT", "10000"))

    # Playwright 페이지 로드 타임아웃 (밀리초)
    PLAYWRIGHT_PAGE_TIMEOUT = int(os.getenv("PLAYWRIGHT_PAGE_TIMEOUT", "30000"))

    # ==================== 로깅 설정 ====================
    # 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # 로그 파일 저장 여부
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True") == "True"

    @classmethod
    def validate(cls):
        """
        설정 유효성 검증

        Raises:
            ValueError: 필수 설정이 누락되거나 잘못된 경우
        """
        if not cls.NAVER_IDS or cls.NAVER_IDS == ['']:
            raise ValueError("NAVER_ID is required in .env file")

        if not cls.NAVER_PWS or cls.NAVER_PWS == ['']:
            raise ValueError("NAVER_PW is required in .env file")

        if len(cls.NAVER_IDS) != len(cls.NAVER_PWS):
            raise ValueError("Number of NAVER_ID and NAVER_PW must match")

        if cls.CAMPAIGN_RETENTION_DAYS < 1:
            raise ValueError("CAMPAIGN_RETENTION_DAYS must be >= 1")

        if cls.USER_SESSION_RETENTION_DAYS < 1:
            raise ValueError("USER_SESSION_RETENTION_DAYS must be >= 1")

        if cls.PAGE_WAIT_SHORT < 0:
            raise ValueError("PAGE_WAIT_SHORT must be >= 0")

        if cls.PAGE_WAIT_LONG < 0:
            raise ValueError("PAGE_WAIT_LONG must be >= 0")

    @classmethod
    def print_config(cls):
        """현재 설정을 출력합니다 (민감 정보 제외)"""
        print("=" * 50)
        print("NaverPaper Configuration")
        print("=" * 50)
        print(f"NAVER_IDS: {len(cls.NAVER_IDS)} accounts")
        print(f"TELEGRAM_ENABLED: {bool(cls.TELEGRAM_TOKEN and cls.TELEGRAM_CHAT_ID)}")
        print(f"NO_PAPER_ALARM: {cls.NO_PAPER_ALARM}")
        print(f"CAMPAIGN_RETENTION_DAYS: {cls.CAMPAIGN_RETENTION_DAYS}")
        print(f"USER_SESSION_RETENTION_DAYS: {cls.USER_SESSION_RETENTION_DAYS}")
        print(f"PAGE_WAIT_SHORT: {cls.PAGE_WAIT_SHORT}s")
        print(f"PAGE_WAIT_LONG: {cls.PAGE_WAIT_LONG}s")
        print(f"LOGIN_WAIT_TIMEOUT: {cls.LOGIN_WAIT_TIMEOUT}s")
        print(f"LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"LOG_TO_FILE: {cls.LOG_TO_FILE}")
        print("=" * 50)


# 모듈 import 시 설정 검증 (선택적)
if __name__ != "__main__":
    # 운영 환경에서는 검증을 자동으로 실행
    # 개발/테스트 시에는 이 줄을 주석 처리 가능
    pass  # Config.validate()


if __name__ == "__main__":
    # config.py를 직접 실행하면 설정 출력
    try:
        Config.validate()
        Config.print_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
