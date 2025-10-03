# src/optiv_lib/providers/pan/objects/address/parser.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from .model import AddressKind, AddressObject
from optiv_lib.providers.pan.util import as_list, collect_members, node_text, yn_bool


class AddressParseError(ValueError):
    """Raised when an address <entry> cannot be parsed in strict mode."""


KIND_FIELDS: Tuple[AddressKind, ...] = ("ip-netmask", "ip-range", "ip-wildcard", "fqdn")


# ----------------------------
# XML → model
# ----------------------------

def from_xml(result: Dict[str, Any], *, strict: bool = True) -> List[AddressObject]:
    """
    Convert ops.config_show/get result (inner 'result') into AddressObject items.
    """
    entries = _pick_entries(result)
    objs: List[AddressObject] = []
    for entry in entries:
        try:
            objs.append(_xml_entry_to_model(entry))
        except Exception as exc:
            if strict:
                raise AddressParseError(f"failed to parse address entry: {exc}") from exc
    return objs


def _pick_entries(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Accept either:
      result['address']['entry']  OR  result['entry']
    """
    address_node = result.get("address")
    raw = address_node.get("entry") if isinstance(address_node, dict) and "entry" in address_node else result.get("entry")
    return [e for e in as_list(raw) if isinstance(e, dict)]


def _xml_entry_to_model(entry: Dict[str, Any]) -> AddressObject:
    name = (entry.get("@name") or "").strip()
    if not name:
        raise ValueError("missing @name")

    kind, value = _detect_kind_value(entry)
    description = node_text(entry.get("description"))
    disable_override = yn_bool(node_text(entry.get("disable-override")))
    tags = tuple(collect_members(entry.get("tag")))

    return AddressObject(
        name=name,
        kind=kind,
        value=value,
        description=description,
        tags=tags,
        disable_override=disable_override,
    )


def _detect_kind_value(entry: Dict[str, Any]) -> Tuple[AddressKind, str]:
    present = [(k, node_text(entry.get(k))) for k in KIND_FIELDS]
    hits = [(k, v) for (k, v) in present if v]
    if len(hits) != 1:
        keys = [k for k, _ in hits]
        raise ValueError(
            "entry must contain exactly one of ip-netmask/ip-range/ip-wildcard/fqdn; got " + repr(sorted(keys))
        )
    k, v = hits[0]
    return k, v or ""


# ----------------------------
# JSON → model
# ----------------------------

def from_json_dict(d: Dict[str, Any]) -> AddressObject:
    """
    Convert a JSON-ready dict (from serializer.to_json_dict) into AddressObject.
    """
    name = str(d.get("name") or "").strip()
    if not name:
        raise ValueError("name is required")

    kind = str(d.get("kind") or "").strip()
    if kind not in KIND_FIELDS:
        raise ValueError(f"kind must be one of {KIND_FIELDS}; got {kind!r}")

    value = str(d.get("value") or "").strip()
    if not value:
        raise ValueError("value is required")

    description = d.get("description")
    tags = tuple(e for e in as_list(d.get("tags")) if isinstance(e, str))
    disable_override = bool(d.get("disable_override", False))

    return AddressObject(
        name=name,
        kind=kind,  # type: ignore[assignment]
        value=value,
        description=description,
        tags=tags,
        disable_override=disable_override,
    )


def from_json_list(items: Iterable[Dict[str, Any]], *, strict: bool = True) -> List[AddressObject]:
    out: List[AddressObject] = []
    for it in items:
        try:
            out.append(from_json_dict(it))
        except Exception as exc:
            if strict:
                raise AddressParseError(f"failed to parse address json: {exc}") from exc
    return out
