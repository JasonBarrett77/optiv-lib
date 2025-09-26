# src/optiv_lib/providers/pan/util.py
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

import xmltodict

DEFAULT_FORCE_LIST: Iterable[str | Callable[..., bool]] = ("entry", "member", "line")


def parse_xml(text: str, *, force_list: Iterable | None = None) -> dict:
    return xmltodict.parse(text, force_list=force_list or DEFAULT_FORCE_LIST)


def node_text(node: Any) -> str | None:
    if node is None:
        return None
    if isinstance(node, dict):
        node = node.get("#text")
    s = ("" if node is None else str(node)).strip()
    return s or None


def as_list(x: Any) -> list[Any]:
    return x if isinstance(x, list) else ([] if x is None else [x])


def yn_bool(s: str | None) -> bool:
    return s is not None and s.strip().lower() in {"y", "yes", "true", "1"}


def attr(node: Dict[str, Any], name: str) -> str | None:
    v = node.get(f"@{name}")
    return None if v is None else str(v).strip()


def collect_members(tag_node: Any) -> list[str]:
    if not isinstance(tag_node, dict):
        return []
    return [v for v in (node_text(m) for m in as_list(tag_node.get("member"))) if v]


def xpath_dg_address(device_group: str) -> str:
    # PAN names disallow quotes, so direct insert is safe
    return f"/config/devices/entry/device-group/entry[@name='{device_group}']/address"
