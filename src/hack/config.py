import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
_SHELL_VARS = set(os.environ)  # set in the shell before start; these win over .env


def load_env() -> None:
    """(Re)read .env into the environment. The app's Reload button calls this, so edits to
    .env apply without a restart. Shell variables still win, so `LLM_PROVIDER=mock uv run ...`
    keeps working."""
    for key, value in dotenv_values(ROOT / ".env").items():
        if key not in _SHELL_VARS and value is not None:
            os.environ[key] = value


load_env()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def data_dir() -> Path:
    return ROOT / env("DATA_DIR", "data/sample")


EXPORTS_DIR = ROOT / "exports"
