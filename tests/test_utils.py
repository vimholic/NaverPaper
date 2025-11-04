"""
Utils 모듈 테스트
"""
import os
import tempfile
import pytest
from utils.logger import setup_logger, get_log_filename
from utils.common import get_random_ua, UA_STRINGS


class TestLogger:
    """Logger 모듈 테스트"""

    def test_setup_logger_console_only(self):
        """콘솔 전용 로거 생성 테스트"""
        logger = setup_logger('test_console')
        assert logger.name == 'test_console'
        assert len(logger.handlers) >= 1

    def test_setup_logger_with_file(self):
        """파일 로깅 포함 로거 생성 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name

        try:
            logger = setup_logger('test_file', log_file)
            assert logger.name == 'test_file'
            assert len(logger.handlers) >= 2  # console + file

            # 로그 작성 테스트
            logger.info("테스트 로그 메시지")

            # 파일에 로그가 기록되었는지 확인
            assert os.path.exists(log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "테스트 로그 메시지" in content

        finally:
            # 테스트 파일 삭제
            if os.path.exists(log_file):
                os.remove(log_file)

    def test_get_log_filename(self):
        """로그 파일명 생성 테스트"""
        log_file = get_log_filename('test')
        assert log_file.startswith('logs/test_')
        assert log_file.endswith('.log')
        assert '2025' in log_file  # 현재 연도 포함

    def test_logger_levels(self):
        """로그 레벨 테스트"""
        import logging
        logger = setup_logger('test_levels', level=logging.DEBUG)
        assert logger.level == logging.DEBUG

        logger = setup_logger('test_levels_info', level=logging.INFO)
        assert logger.level == logging.INFO


class TestCommon:
    """Common 모듈 테스트"""

    def test_get_random_ua(self):
        """랜덤 User-Agent 생성 테스트"""
        ua = get_random_ua()
        assert ua in UA_STRINGS
        assert isinstance(ua, str)
        assert len(ua) > 0
        assert 'Mozilla' in ua

    def test_get_random_ua_randomness(self):
        """User-Agent 랜덤성 테스트"""
        # 100번 호출하면 적어도 2개 이상의 다른 UA가 나와야 함
        uas = [get_random_ua() for _ in range(100)]
        unique_uas = set(uas)
        assert len(unique_uas) >= 2

    def test_ua_strings_count(self):
        """UA 문자열 개수 테스트"""
        assert len(UA_STRINGS) == 9

    def test_ua_strings_valid(self):
        """모든 UA 문자열 유효성 테스트"""
        for ua in UA_STRINGS:
            assert isinstance(ua, str)
            assert len(ua) > 0
            assert 'Mozilla' in ua
            assert 'AppleWebKit' in ua or 'Gecko' in ua


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
