"""profile.yaml 로딩."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Profile


def load_profile(path: str | Path = "profile.yaml") -> Profile:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"프로파일이 없습니다: {path}\n"
            "profile.example.yaml 을 복사해 만드세요: cp profile.example.yaml profile.yaml"
        )
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Profile.model_validate(data)
