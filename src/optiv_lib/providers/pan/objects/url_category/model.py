# src/optiv_lib/providers/pan/objects/url_category/model.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence, Tuple

# ----------------------------
# Types
# ----------------------------

UrlCategoryType = Literal["URL List", "Category Match"]
ConfigSource = Literal["running", "candidate"]  # provenance only


# ----------------------------
# Normalization helpers
# ----------------------------

def _normalize_urls(urls: Sequence[str]) -> tuple[str, ...]:
    """
    Trim, drop empties, dedupe (case-sensitive to preserve intent), sort case-insensitively.
    """
    trimmed = (s.strip() for s in urls)
    kept = [s for s in trimmed if s]
    # dedupe preserving first occurrence
    seen: set[str] = set()
    dedup: list[str] = []
    for s in kept:
        if s not in seen:
            seen.add(s)
            dedup.append(s)
    return tuple(sorted(dedup, key=lambda s: s.casefold()))


def _normalize_categories(categories: Sequence[str]) -> tuple[str, ...]:
    """
    Categories are canonical lowercase hyphenated names.
    Trim, lower, drop empties, dedupe case-insensitively, sort case-insensitively.
    """
    trimmed_lower = (s.strip().lower() for s in categories)
    kept = [s for s in trimmed_lower if s]
    seen: set[str] = set()
    dedup: list[str] = []
    for s in kept:
        key = s.casefold()
        if key not in seen:
            seen.add(key)
            dedup.append(s)
    return tuple(sorted(dedup, key=lambda s: s.casefold()))


# ----------------------------
# Diff model
# ----------------------------

@dataclass(slots=True, frozen=True)
class UrlCategoryDiff:
    """Field-wise delta for sync planning."""
    different: bool
    changed_fields: Tuple[str, ...]
    changes: dict[str, tuple[object, object]]  # field -> (from, to)


# ----------------------------
# URL Category model
# ----------------------------

@dataclass(slots=True, frozen=True, order=True)
class UrlCategoryObject:
    """
    PAN-OS Custom URL Category (immutable).

    Two shapes:
      - type == "URL List"       → use `urls`
      - type == "Category Match" → use `categories`

    Scope:
      - shared       → device_group is None
      - device-group → device_group holds the DG name

    Provenance:
      - source: "running" or "candidate"
    """
    name: str
    type: UrlCategoryType

    # One of these is used depending on `type`
    urls: Sequence[str] = field(default_factory=tuple)
    categories: Sequence[str] = field(default_factory=tuple)

    description: Optional[str] = None

    device_group: Optional[str] = None
    source: ConfigSource = "running"

    # ---- invariants ----
    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name required")

        # Normalize collections
        norm_urls = _normalize_urls(self.urls)
        norm_categories = _normalize_categories(self.categories)
        object.__setattr__(self, "urls", norm_urls)
        object.__setattr__(self, "categories", norm_categories)

        # Enforce mutually exclusive shape
        if self.type == "URL List":
            if not self.urls:
                raise ValueError("URL List category requires at least one url")
            if self.categories:
                raise ValueError("URL List category must not define categories")
        elif self.type == "Category Match":
            if not self.categories:
                raise ValueError("Category Match category requires at least one category")
            if self.urls:
                raise ValueError("Category Match category must not define urls")
        else:
            raise ValueError(f"invalid type: {self.type}")

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
        """
        Canonical content identity excluding name/scope/source.
        """
        return (
            self.type, self.urls, self.categories, self.description or "",
            )

    # ---- diff ----
    def diff(self, other: UrlCategoryObject) -> UrlCategoryDiff:
        changes: dict[str, tuple[object, object]] = {}
        for f in ("name", "type", "urls", "categories", "description"):
            a, b = getattr(self, f), getattr(other, f)
            if a != b:
                changes[f] = (a, b)
        return UrlCategoryDiff(different=bool(changes), changed_fields=tuple(sorted(changes)), changes=changes, )
