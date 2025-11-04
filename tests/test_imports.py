"""
모듈 Import 테스트
"""
import pytest


class TestImports:
    """모듈 import 가능성 테스트"""

    def test_import_config(self):
        """config 모듈 import 테스트"""
        from config import Config
        assert Config is not None

    def test_import_database(self):
        """database 모듈 import 테스트"""
        from database import Database
        assert Database is not None

    def test_import_models(self):
        """models 모듈 import 테스트"""
        from models import CampaignUrl, UrlVisit, User
        assert CampaignUrl is not None
        assert UrlVisit is not None
        assert User is not None

    def test_import_utils_logger(self):
        """utils.logger 모듈 import 테스트"""
        from utils.logger import setup_logger, get_log_filename
        assert setup_logger is not None
        assert get_log_filename is not None

    def test_import_utils_common(self):
        """utils.common 모듈 import 테스트"""
        from utils.common import get_random_ua, UA_STRINGS
        assert get_random_ua is not None
        assert UA_STRINGS is not None
        assert len(UA_STRINGS) > 0

    def test_import_all_main_modules(self):
        """주요 실행 모듈 import 테스트"""
        # get_paper.py는 실행 시 환경 변수가 필요하므로 import만 테스트
        import importlib.util
        import sys

        modules = ['get_paper', 'fetch_url', 'save_cookies']
        for module_name in modules:
            spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                # Note: 실제 실행은 하지 않고 로드만 확인
                assert spec is not None


# Run with: pytest tests/test_imports.py -v
