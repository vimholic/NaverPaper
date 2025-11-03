"""
공통 유틸리티 함수 모듈

기능:
- User-Agent 문자열 관리
- 공통 상수 및 헬퍼 함수
"""
import random


# User-Agent 문자열 목록 (모바일 디바이스)
UA_STRINGS = [
    "Mozilla/5.0 (Linux; Android 12; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.61 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.153 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; M2006C3LG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/19.0 Chrome/102.0.5005.125 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/103.0.5060.63 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Lenovo TB-J606F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Safari/537.36",
]


def get_random_ua():
    """
    랜덤한 User-Agent 문자열을 반환합니다.

    봇 탐지를 우회하기 위해 매 요청마다 다른 User-Agent를 사용합니다.
    모바일 디바이스의 User-Agent만 포함되어 있습니다.

    Returns:
        str: 랜덤하게 선택된 User-Agent 문자열

    Example:
        >>> ua = get_random_ua()
        >>> headers = {'User-Agent': ua}
    """
    return random.choice(UA_STRINGS)
