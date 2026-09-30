import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
_SHELL_VARS = set(os.environ)  # set in the shell before start; these win over .env
_FROM_DOTENV: set[str] = set()  # keys the last load took from .env


def load_env() -> None:
    """(Re)read .env into the environment, including removed or commented-out lines. Shell
    variables still win, so `LLM_PROVIDER=mock uv run ...` keeps working."""
    values = {
        key: value
        for key, value in dotenv_values(ROOT / ".env").items()
        if key not in _SHELL_VARS and value is not None
    }
    for key in _FROM_DOTENV - values.keys():
        os.environ.pop(key, None)
    os.environ.update(values)
    _FROM_DOTENV.clear()
    _FROM_DOTENV.update(values)


load_env()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def data_dir() -> Path:
    return ROOT / env("DATA_DIR", "data/sample")
