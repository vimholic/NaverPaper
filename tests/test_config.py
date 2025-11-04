"""
Config 모듈 테스트
"""
import os
import pytest
from config import Config


class TestConfig:
    """Config 클래스 테스트"""

    def test_default_values(self):
        """기본값 테스트"""
        assert Config.CAMPAIGN_RETENTION_DAYS == 60
        assert Config.USER_SESSION_RETENTION_DAYS == 7
        assert Config.PAGE_WAIT_SHORT == 3
        assert Config.PAGE_WAIT_LONG == 5
        assert Config.LOGIN_WAIT_TIMEOUT == 60
        assert Config.PLAYWRIGHT_NETWORK_TIMEOUT == 10000
        assert Config.PLAYWRIGHT_PAGE_TIMEOUT == 30000
        assert Config.LOG_LEVEL == "INFO"
        assert Config.LOG_TO_FILE is True

    def test_config_validation_success(self):
        """올바른 설정 검증 성공 테스트"""
        # 환경 변수가 설정되어 있으면 검증 성공
        if Config.NAVER_IDS and Config.NAVER_IDS != ['']:
            Config.validate()
        else:
            # 환경 변수가 없으면 검증 실패 예상
            with pytest.raises(ValueError):
                Config.validate()

    def test_config_validation_mismatch_count(self):
        """ID/PW 개수 불일치 테스트"""
        original_ids = Config.NAVER_IDS
        original_pws = Config.NAVER_PWS

        # 강제로 개수 불일치 생성
        Config.NAVER_IDS = ['id1', 'id2']
        Config.NAVER_PWS = ['pw1']

        with pytest.raises(ValueError, match="Number of NAVER_ID and NAVER_PW must match"):
            Config.validate()

        # 원래 값 복원
        Config.NAVER_IDS = original_ids
        Config.NAVER_PWS = original_pws

    def test_config_validation_retention_days(self):
        """보존 기간 검증 테스트"""
        original = Config.CAMPAIGN_RETENTION_DAYS

        Config.CAMPAIGN_RETENTION_DAYS = 0
        with pytest.raises(ValueError, match="CAMPAIGN_RETENTION_DAYS must be >= 1"):
            Config.validate()

        Config.CAMPAIGN_RETENTION_DAYS = -1
        with pytest.raises(ValueError, match="CAMPAIGN_RETENTION_DAYS must be >= 1"):
            Config.validate()

        # 원래 값 복원
        Config.CAMPAIGN_RETENTION_DAYS = original

    def test_config_print(self, capsys):
        """설정 출력 테스트"""
        Config.print_config()
        captured = capsys.readouterr()
        assert "NaverPaper Configuration" in captured.out
        assert "CAMPAIGN_RETENTION_DAYS" in captured.out


# Run with: pytest tests/test_config.py -v
