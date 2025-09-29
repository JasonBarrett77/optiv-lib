# src/optiv_lib/providers/pan/objects/address/model.py
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence

AddressKind = Literal["ip-netmask", "ip-range", "ip-wildcard", "fqdn"]

_FQDN_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?:\.(?!-)[A-Za-z0-9-]{1,63})+$")


def _canon_fqdn(s: str) -> str:
    # FQDNs are case-insensitive; normalize to lowercase.
    return s.strip().lower()


def _normalize_tags(tags: Sequence[str]) -> tuple[str, ...]:
    """
    Trim, dedupe by exact case, preserve original order. No sorting.
    Palo Alto tags are case-sensitive.
    """
    seen: set[str] = set()
    out: list[str] = []
    for raw in tags:
        t = raw.strip()
        if not t:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return tuple(out)


def _validate_value(kind: AddressKind, value: str) -> None:
    if not value:
        raise ValueError("value required")

    if kind == "ip-netmask":
        ipaddress.ip_network(value, strict=False)

    elif kind == "ip-range":
        a, sep, b = value.partition("-")
        if not sep:
            raise ValueError("ip-range must be 'start-end'")
        ia, ib = ipaddress.ip_address(a), ipaddress.ip_address(b)
        if ia.version != ib.version or int(ia) > int(ib):
            raise ValueError("ip-range endpoints invalid")

    elif kind == "ip-wildcard":
        ip_str, sep, mask = value.partition("/")
        if not sep:
            raise ValueError("ip-wildcard must be 'IP/WILDCARD.MASK'")
        ipaddress.IPv4Address(ip_str)
        parts = mask.split(".")
        if len(parts) != 4:
            raise ValueError("wildcard mask must have 4 octets")
        vals = [int(o) for o in parts]
        if not all(0 <= o <= 255 for o in vals):
            raise ValueError("wildcard mask octet out of range")

    elif kind == "fqdn":
        if not _FQDN_RE.match(value):
            raise ValueError("fqdn invalid")

    else:
        raise ValueError(f"invalid kind: {kind}")


@dataclass(slots=True, frozen=True)
class AddressObject:
    name: str
    kind: AddressKind
    value: str

    description: Optional[str] = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    disable_override: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name required")

        _validate_value(self.kind, self.value)

        if self.kind == "fqdn":
            object.__setattr__(self, "value", _canon_fqdn(self.value))

        object.__setattr__(self, "tags", _normalize_tags(self.tags))

    def key(self) -> str:
        return self.name
