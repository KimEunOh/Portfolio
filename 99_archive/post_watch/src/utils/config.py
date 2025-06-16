import json
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class KakaoConfig:
    rest_api_key: str


@dataclass
class AppConfig:
    target_url: str
    crawl_interval_seconds: int
    db_path: str
    openai_api_key: str
    kakao: KakaoConfig

    @classmethod
    def from_dict(cls, data: Dict) -> "AppConfig":
        kakao_config = KakaoConfig(**data["kakao"])
        return cls(
            target_url=data["target_url"],
            crawl_interval_seconds=data["crawl_interval_seconds"],
            db_path=data["db_path"],
            openai_api_key=data["openai_api_key"],
            kakao=kakao_config,
        )


def load_config(path: str = "config/config.json") -> AppConfig:
    """JSON 설정 파일에서 설정을 로드합니다."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        return AppConfig.from_dict(config_data)
    except FileNotFoundError:
        raise Exception(f"설정 파일을 찾을 수 없습니다: {path}")
    except json.JSONDecodeError:
        raise Exception(f"설정 파일의 형식이 올바르지 않습니다: {path}")
    except KeyError as e:
        raise Exception(f"설정 파일에 필요한 키가 없습니다: {e}")


# 전역 설정 객체
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """전역 설정 객체를 반환합니다. 로드되지 않은 경우 로드합니다."""
    global config
    if config is None:
        config = load_config()
    return config
