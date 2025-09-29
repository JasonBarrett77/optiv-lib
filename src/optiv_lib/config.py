from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Union

VerifyType = Union[bool, str]  # bool or CA bundle path


def _resolve(v: Any) -> Any:
    if isinstance(v, dict) and "env" in v:
        return os.getenv(str(v["env"]), v.get("default"))
    return v


def _as_verify(v: Any) -> VerifyType:
    v = _resolve(v)
    if isinstance(v, bool) or v is None:
        return True if v is None else v
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return str(v)  # CA bundle path


def _as_float(v: Any, default: float) -> float:
    v = _resolve(v)
    return default if v is None else float(v)


@dataclass(slots=True, frozen=True)
class Secret:
    """Callable-backed secret; masked in str/repr."""
    _provider: Callable[[], str]

    def get(self) -> str:
        return self._provider()

    def __repr__(self) -> str:
        return "******"

    def __str__(self) -> str:
        return "******"


def _secret_from(node: Any) -> Secret:
    if isinstance(node, dict) and "env" in node:
        env = str(node["env"]); default = node.get("default")
        return Secret(lambda: os.getenv(env, default) or "")
    lit = _resolve(node)
    return Secret(lambda: "" if lit is None else str(lit))


@dataclass(slots=True, frozen=True)
class PanoramaConfig:
    hostname: str
    username: str
    password: Secret
    verify: VerifyType = True
    timeout: float = 15.0


@dataclass(slots=True, frozen=True)
class Extras:
    """Read-only attribute access to app-level keys under 'app'."""
    data: Mapping[str, Any]

    def __getattr__(self, name: str) -> Any:
        d = object.__getattribute__(self, "data")
        if name in d:
            return d[name]
        raise AttributeError(name)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def keys(self) -> Any:
        return self.data.keys()

    def __contains__(self, key: str) -> bool:
        return key in self.data


@dataclass(slots=True, frozen=True)
class AppConfig:
    panorama: Optional[PanoramaConfig] = None
    extras: Extras = field(default_factory=lambda: Extras(MappingProxyType({})))

    @classmethod
    def from_json(cls, path: Path | str) -> "AppConfig":
        p = Path(path)
        data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))

        pano_cfg = None
        pano_src = data.get("panorama")
        if isinstance(pano_src, dict):
            h = _resolve(pano_src.get("hostname"))
            u = _resolve(pano_src.get("username"))
            pw = _secret_from(pano_src.get("password"))
            if h and u and pw:
                pano_cfg = PanoramaConfig(
                    hostname=str(h),
                    username=str(u),
                    password=pw,
                    verify=_as_verify(pano_src.get("verify")),
                    timeout=_as_float(pano_src.get("timeout"), 15.0),
                )

        extras_raw = data.get("app", {}) or {}
        extras = Extras(MappingProxyType(extras_raw))

        return cls(panorama=pano_cfg, extras=extras)

    @property
    def panorama_required(self) -> PanoramaConfig:
        if not self.panorama:
            raise ValueError("Panorama config missing")
        return self.panorama
