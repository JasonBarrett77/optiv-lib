# src/optiv_lib/providers/pan/session_from_json.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from optiv_lib.providers.pan.session import PanoramaSession

VerifyType = bool | str  # bool or CA bundle path


def session_from_json(path: Path) -> PanoramaSession:
    """
    Create a PanoramaSession from a JSON config file.

    The JSON may specify values directly or via environment variables.

    Accepted shapes (top-level or under {"panorama": {...}}):
      {
        "hostname": "pan.example.com" | {"env": "PANORAMA_HOSTNAME", "default": "pan.example.com"},
        "username": "admin"           | {"env": "PANORAMA_USERNAME"},
        "password": "secret"          | {"env": "PANORAMA_PASSWORD"},
        "verify":   true              | false | "/path/to/ca.pem" | {"env": "PANORAMA_VERIFY", "default": "true"}
      }

    Rules:
      - hostname, username, password are required after resolution.
      - verify can be:
          True/False, a CA bundle path string, or env that resolves to one of those.
        Strings "true/false/1/0/yes/no/on/off" (case-insensitive) coerce to bool;
        any other string is treated as a path.

    Raises:
      ValueError on missing or invalid required fields.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cfg = raw.get("panorama", raw)  # allow nesting under "panorama"

    hostname = _resolve(cfg.get("hostname"))
    username = _resolve(cfg.get("username"))
    password = _resolve(cfg.get("password"))
    verify = _resolve_verify(cfg.get("verify"))

    if not isinstance(hostname, str) or not hostname:
        raise ValueError("hostname is required")
    if not isinstance(username, str) or not username:
        raise ValueError("username is required")
    if not isinstance(password, str) or not password:
        raise ValueError("password is required")

    return PanoramaSession(
        hostname=hostname,
        username=username,
        password=password,
        verify=True if verify is None else verify,
    )


# -----------------
# helpers
# -----------------

def _resolve(node: Any) -> Any:
    """Resolve a value or {'env': NAME, 'default': X} using os.environ."""
    if isinstance(node, dict) and "env" in node:
        env_name = str(node["env"])
        default = node.get("default")
        return os.getenv(env_name, default)
    return node


def _resolve_verify(node: Any) -> Optional[VerifyType]:
    """
    Resolve 'verify' which can be bool, path string, or {'env': ...}.
    Coerce common truthy/falsey strings to bool; otherwise return string.
    """
    v = _resolve(node)
    if v is None or isinstance(v, bool):
        return v  # None -> use default True upstream
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return str(v)  # treat as CA bundle path
