import json
import os
import unittest
from unittest.mock import patch, mock_open

from src.utils.config import load_config, AppConfig, KakaoConfig, get_config


class TestConfig(unittest.TestCase):

    def setUp(self):
        """테스트를 위한 임시 설정 파일을 생성합니다."""
        self.config_data = {
            "target_url": "http://test.com",
            "crawl_interval_seconds": 30,
            "db_path": "test.db",
            "openai_api_key": "test_key",
            "kakao": {"rest_api_key": "kakao_test_key"},
        }
        self.config_path = "test_config.json"
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f)

    def tearDown(self):
        """테스트 종료 후 임시 설정 파일을 삭제합니다."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        # Reset global config
        from src.utils import config as config_module

        config_module.config = None

    def test_load_config_success(self):
        """설정 파일 로딩이 성공하는지 테스트합니다."""
        config = load_config(self.config_path)
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.target_url, "http://test.com")
        self.assertEqual(config.crawl_interval_seconds, 30)
        self.assertIsInstance(config.kakao, KakaoConfig)
        self.assertEqual(config.kakao.rest_api_key, "kakao_test_key")

    def test_load_config_file_not_found(self):
        """설정 파일이 없을 때 예외가 발생하는지 테스트합니다."""
        with self.assertRaisesRegex(Exception, "설정 파일을 찾을 수 없습니다"):
            load_config("non_existent_file.json")

    def test_load_config_invalid_json(self):
        """설정 파일이 잘못된 JSON 형식일 때 예외가 발생하는지 테스트합니다."""
        with open("invalid.json", "w") as f:
            f.write("{'key': 'value'}")  # Invalid JSON

        with self.assertRaisesRegex(Exception, "설정 파일의 형식이 올바르지 않습니다"):
            load_config("invalid.json")

        os.remove("invalid.json")

    def test_load_config_missing_key(self):
        """설정 파일에 필수 키가 없을 때 예외가 발생하는지 테스트합니다."""
        del self.config_data["target_url"]
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f)

        with self.assertRaisesRegex(Exception, "설정 파일에 필요한 키가 없습니다"):
            load_config(self.config_path)

    @patch("src.utils.config.load_config")
    def test_get_config_loads_once(self, mock_load_config):
        """get_config가 설정을 한 번만 로드하는지 테스트합니다."""
        mock_load_config.return_value = AppConfig.from_dict(self.config_data)

        # 첫 번째 호출 - load_config가 호출되어야 함
        config1 = get_config()
        mock_load_config.assert_called_once()

        # 두 번째 호출 - load_config가 다시 호출되지 않아야 함
        config2 = get_config()
        mock_load_config.assert_called_once()

        self.assertIs(config1, config2)


if __name__ == "__main__":
    unittest.main()
