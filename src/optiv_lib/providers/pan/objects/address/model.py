# src/optiv_lib/providers/pan/objects/address/model.py
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence, Tuple

# ----------------------------
# Types
# ----------------------------

AddressKind = Literal["ip-netmask", "ip-range", "ip-wildcard", "fqdn"]
ConfigSource = Literal["running", "candidate"]  # provenance only

# ----------------------------
# Validation helpers
# ----------------------------

_FQDN_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?:\.(?!-)[A-Za-z0-9-]{1,63})+$", )


def _canon_fqdn(s: str) -> str:
    return s.strip().lower()


def _normalize_tags(tags: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    trimmed = (x.strip() for x in tags)
    dedup = (t for t in trimmed if t and (t.lower() not in seen and not seen.add(t.lower())))
    return tuple(sorted(dedup, key=lambda s: s.casefold()))


def _validate_value(kind: AddressKind, value: str) -> None:
    if not value:
        raise ValueError("value required")

    if kind == "ip-netmask":
        # Accept IPv4/IPv6 CIDR
        ipaddress.ip_network(value, strict=False)

    elif kind == "ip-range":
        # Expect "A.B.C.D-W.X.Y.Z" or IPv6 "start-end"
        a, sep, b = value.partition("-")
        if not sep:
            raise ValueError("ip-range must be 'start-end'")
        ia, ib = ipaddress.ip_address(a), ipaddress.ip_address(b)
        if ia.version != ib.version or int(ia) > int(ib):
            raise ValueError("ip-range endpoints invalid")

    elif kind == "ip-wildcard":
        # PAN-OS wildcard mask is IPv4 only: "IP/WILDCARD.MASK"
        ip_str, sep, mask = value.partition("/")
        if not sep:
            raise ValueError("ip-wildcard must be 'IP/WILDCARD.MASK'")
        ipaddress.IPv4Address(ip_str)
        parts = mask.split(".")
        if len(parts) != 4:
            raise ValueError("wildcard mask must have 4 octets")
        try:
            vals = [int(o) for o in parts]
        except ValueError as e:
            raise ValueError("wildcard mask contains non-integers") from e
        if not all(0 <= o <= 255 for o in vals):
            raise ValueError("wildcard mask octet out of range")

    elif kind == "fqdn":
        if not _FQDN_RE.match(value):
            raise ValueError("fqdn invalid")

    else:
        raise ValueError(f"invalid kind: {kind}")


# ----------------------------
# Diff model
# ----------------------------

@dataclass(slots=True, frozen=True)
class AddressDiff:
    """Field-wise delta for sync planning."""
    different: bool
    changed_fields: Tuple[str, ...]
    changes: dict[str, tuple[object, object]]  # field -> (from, to)


# ----------------------------
# Address model
# ----------------------------

@dataclass(slots=True, frozen=True, order=True)
class AddressObject:
    """
    PAN-OS Address (pure, immutable).

    Scope:
      - shared       → device_group is None
      - device-group → device_group holds the DG name

    Provenance:
      - source: "running" or "candidate"
    """
    name: str
    kind: AddressKind
    value: str

    description: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    disable_override: bool = False

    device_group: Optional[str] = None
    source: ConfigSource = "running"

    # ---- invariants ----
    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name required")

        _validate_value(self.kind, self.value)

        if self.kind == "fqdn":
            object.__setattr__(self, "value", _canon_fqdn(self.value))

        # normalize → tuple
        object.__setattr__(self, "tags", _normalize_tags(self.tags))

        # # normalize tags: trim, dedupe (case-insensitive), sort (case-insensitive)
        # seen: set[str] = set()
        # trimmed = (x.strip() for x in self.tags)
        # dedup = (t for t in trimmed if t and (t.lower() not in seen and not seen.add(t.lower())))
        # norm = tuple(sorted(dedup, key=lambda s: s.casefold()))
        # if norm != self.tags:
        #     object.__setattr__(self, "tags", norm)

    # ---- scope helpers ----
    @property
    def shared(self) -> bool:
        return self.device_group is None

    def scope_key(self) -> tuple[str, Optional[str]]:
        return (self.name, self.device_group)

    # ---- identity ----
    def key(self) -> tuple[str]:
        return (self.name,)

    def natural_key(self) -> tuple:
        return self.kind, self.value, self.description or "", self.tags, self.disable_override

    # ---- diff ----
    def diff(self, other: AddressObject) -> AddressDiff:
        changes: dict[str, tuple[object, object]] = {}
        for f in ("name", "kind", "value", "description", "tags", "disable_override"):
            a, b = getattr(self, f), getattr(other, f)
            if a != b:
                changes[f] = (a, b)
        return AddressDiff(different=bool(changes), changed_fields=tuple(sorted(changes)), changes=changes, )
