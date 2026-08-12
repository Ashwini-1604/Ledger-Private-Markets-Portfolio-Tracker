"""Configuration: reads from ~/.commitgen/config.toml, falling back to
environment variables. Keeps API keys out of shell history / repo files."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".commitgen"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_MODEL = "claude-sonnet-4-6"

VALID_STYLES = ("conventional", "gitmoji", "plain")


@dataclass
class Config:
    api_key: str | None = None
    model: str = DEFAULT_MODEL
    style: str = "conventional"
    max_subject_length: int = 72
    include_body: bool = True


def load_config() -> Config:
    cfg = Config()

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
        cfg.api_key = data.get("api_key", cfg.api_key)
        cfg.model = data.get("model", cfg.model)
        cfg.style = data.get("style", cfg.style)
        cfg.max_subject_length = data.get("max_subject_length", cfg.max_subject_length)
        cfg.include_body = data.get("include_body", cfg.include_body)

    # Environment variables override the config file
    cfg.api_key = os.environ.get("ANTHROPIC_API_KEY", cfg.api_key)
    cfg.model = os.environ.get("COMMITGEN_MODEL", cfg.model)
    cfg.style = os.environ.get("COMMITGEN_STYLE", cfg.style)

    return cfg


def write_default_config(api_key: str, style: str = "conventional") -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        f'api_key = "{api_key}"\n'
        f'model = "{DEFAULT_MODEL}"\n'
        f'style = "{style}"\n'
        f'max_subject_length = 72\n'
        f'include_body = true\n'
    )
    # Restrict permissions since this file holds a secret
    os.chmod(CONFIG_PATH, 0o600)
