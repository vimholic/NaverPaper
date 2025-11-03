"""
로깅 시스템 설정 모듈

기능:
- 콘솔 및 파일 로깅 지원
- 로그 레벨별 필터링 (DEBUG, INFO, WARNING, ERROR)
- UTF-8 인코딩 지원 (한글 로그)
- 타임스탬프 자동 추가
"""
import logging
import os
from datetime import datetime


def setup_logger(name, log_file=None, level=logging.INFO):
    """
    로거를 설정하고 반환합니다.

    Args:
        name (str): 로거 이름 (보통 모듈명 __name__ 사용)
        log_file (str, optional): 로그 파일 경로. None이면 파일 저장 안 함.
        level (int, optional): 로그 레벨. 기본값은 INFO.

    Returns:
        logging.Logger: 설정된 로거 인스턴스

    Example:
        >>> logger = setup_logger(__name__, 'app.log')
        >>> logger.info("애플리케이션 시작")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (선택)
    if log_file:
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_log_filename(prefix='naverpaper'):
    """
    날짜 기반 로그 파일명을 생성합니다.

    Args:
        prefix (str): 로그 파일명 접두사

    Returns:
        str: 로그 파일 경로 (예: logs/naverpaper_2025-01-03.log)
    """
    today = datetime.now().strftime('%Y-%m-%d')
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f'{prefix}_{today}.log')
