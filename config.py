import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env"
DEFAULT_COPILOT_MODEL = "claude*sonnet*"
COPILOT_MODELS = [
    "claude*sonnet*",
    "gpt*",
    "gemini*",
    "raptor*",
]


def _safe_getenv(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv

        if ENV_FILE.exists():
            load_dotenv(ENV_FILE, override=False)
    except Exception:
        # Keep startup resilient even when dotenv is not installed.
        pass


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    env_file: Path
    viralcutter_host: str
    ort_logging_level: str
    tf_cpp_min_log_level: str
    copilot_github_token: str
    gh_token: str
    github_token: str
    copilot_oauth_client_id: str
    copilot_oauth_client_secret: str

    @property
    def copilot_token(self) -> str:
        token, _ = self.resolve_copilot_token()
        return token

    @property
    def copilot_token_source(self) -> str:
        _, source = self.resolve_copilot_token()
        return source

    def resolve_copilot_token(self) -> Tuple[str, str]:
        if self.copilot_github_token:
            return self.copilot_github_token, "COPILOT_GITHUB_TOKEN"
        if self.gh_token:
            return self.gh_token, "GH_TOKEN"
        if self.github_token:
            return self.github_token, "GITHUB_TOKEN"
        return "", ""


_APP_CONFIG = None


def build_app_config() -> AppConfig:
    return AppConfig(
        root_dir=ROOT_DIR,
        env_file=ENV_FILE,
        viralcutter_host=_safe_getenv("VIRALCUTTER_HOST", "0.0.0.0"),
        ort_logging_level=_safe_getenv("ORT_LOGGING_LEVEL", "3"),
        tf_cpp_min_log_level=_safe_getenv("TF_CPP_MIN_LOG_LEVEL", "3"),
        copilot_github_token=_safe_getenv("COPILOT_GITHUB_TOKEN"),
        gh_token=_safe_getenv("GH_TOKEN"),
        github_token=_safe_getenv("GITHUB_TOKEN"),
        copilot_oauth_client_id=_safe_getenv("COPILOT_OAUTH_CLIENT_ID"),
        copilot_oauth_client_secret=_safe_getenv(
            "COPILOT_OAUTH_CLIENT_SECRET"
        ),
    )


def get_app_config(force_reload: bool = False) -> AppConfig:
    global _APP_CONFIG
    if force_reload or _APP_CONFIG is None:
        _APP_CONFIG = build_app_config()
    return _APP_CONFIG


def initialize_environment() -> AppConfig:
    _load_dotenv_if_available()
    config = get_app_config(force_reload=True)
    os.environ.setdefault("ORT_LOGGING_LEVEL", config.ort_logging_level)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", config.tf_cpp_min_log_level)
    return config
