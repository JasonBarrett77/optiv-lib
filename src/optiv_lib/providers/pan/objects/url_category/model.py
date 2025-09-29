# src/optiv_lib/providers/pan/objects/url_category/model.py
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal, cast
from urllib.parse import SplitResult, urlsplit, urlunsplit

UrlCategoryType = Literal["URL List", "Category Match"]
Transform = Callable[[str], str]


def _normalize_keep_order(values: Sequence[str], *, transform: Transform | None = None) -> tuple[str, ...]:
    """Trim, optional transform, dedupe preserving first occurrence and case, keep order."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        v = raw.strip()
        if not v:
            continue
        if transform:
            v = transform(v)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return tuple(out)


def _normalize_url_entry(entry: str) -> str:
    """
    If the entry has a host and an empty path, ensure trailing '/'.
    Preserve case and all other components. Handle bare hostnames.
    """
    s = entry.strip()
    if not s:
        return s

    if "://" not in s and not s.startswith("//") and "/" not in s and "?" not in s and "#" not in s:
        return s + "/"

    parts: SplitResult = urlsplit(s, allow_fragments=True)
    if parts.netloc and parts.path == "":
        parts = parts._replace(path="/")

    return cast(str, urlunsplit(parts))


@dataclass(slots=True, frozen=True)
class UrlCategoryObject:
    """
    PAN-OS Custom URL Category.

    type == "URL List"       → urls is used
    type == "Category Match" → categories is used
    """
    name: str
    type: UrlCategoryType
    urls: tuple[str, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name required")

        object.__setattr__(self, "urls", _normalize_keep_order(self.urls, transform=_normalize_url_entry))
        object.__setattr__(self, "categories", _normalize_keep_order(self.categories))

        if self.type == "URL List":
            if not self.urls:
                raise ValueError("URL List requires at least one url")
            if self.categories:
                raise ValueError("URL List must not define categories")
        elif self.type == "Category Match":
            if not self.categories:
                raise ValueError("Category Match requires at least one category")
            if self.urls:
                raise ValueError("Category Match must not define urls")
        else:
            raise ValueError(f"invalid type: {self.type}")

    def key(self) -> str:
        return self.name
