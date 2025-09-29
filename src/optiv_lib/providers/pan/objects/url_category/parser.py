# src/optiv_lib/providers/pan/objects/url_category/parser.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .model import UrlCategoryObject, UrlCategoryType
from optiv_lib.providers.pan.util import as_list, collect_members, node_text


class UrlCategoryParseError(ValueError):
    """Raised when a url-category <entry> cannot be parsed in strict mode."""


# ----------------------------
# XML → model
# ----------------------------

def from_xml(result: Dict[str, Any], *, strict: bool = True) -> List[UrlCategoryObject]:
    """
    Convert ops.config_show/get result (inner 'result') into UrlCategoryObject items.
    """
    entries = _pick_entries(result)
    objs: List[UrlCategoryObject] = []
    for entry in entries:
        try:
            objs.append(_xml_entry_to_model(entry))
        except Exception as exc:
            if strict:
                raise UrlCategoryParseError(f"failed to parse url-category entry: {exc}") from exc
    return objs


def _pick_entries(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Accept either:
      result['custom-url-category']['entry']  OR  result['entry']
    """
    cuc = result.get("custom-url-category")
    raw = cuc.get("entry") if isinstance(cuc, dict) and "entry" in cuc else result.get("entry")
    return [e for e in as_list(raw) if isinstance(e, dict)]


def _xml_entry_to_model(entry: Dict[str, Any]) -> UrlCategoryObject:
    name = (entry.get("@name") or "").strip()
    if not name:
        raise ValueError("missing @name")

    type_text = node_text(entry.get("type")) or "URL List"
    type_val: UrlCategoryType = "Category Match" if type_text.strip() == "Category Match" else "URL List"

    description = node_text(entry.get("description"))
    members = collect_members(entry.get("list"))
    if type_val == "URL List":
        return UrlCategoryObject(name=name, type=type_val, urls=tuple(members), description=description)
    else:
        return UrlCategoryObject(name=name, type=type_val, categories=tuple(members), description=description)


# ----------------------------
# JSON → model
# ----------------------------

def from_json_dict(d: Dict[str, Any]) -> UrlCategoryObject:
    """
    Convert a JSON-ready dict (from serializer.to_json_dict) into UrlCategoryObject.
    """
    name = str(d.get("name") or "").strip()
    if not name:
        raise ValueError("name is required")

    type_text = str(d.get("type") or "URL List").strip()
    type_val: UrlCategoryType = "Category Match" if type_text == "Category Match" else "URL List"

    desc = d.get("description")
    if type_val == "URL List":
        urls = tuple(e for e in as_list(d.get("urls")) if isinstance(e, str))
        return UrlCategoryObject(name=name, type=type_val, urls=urls, description=desc)
    else:
        cats = tuple(e for e in as_list(d.get("categories")) if isinstance(e, str))
        return UrlCategoryObject(name=name, type=type_val, categories=cats, description=desc)


def from_json_list(items: Iterable[Dict[str, Any]], *, strict: bool = True) -> List[UrlCategoryObject]:
    out: List[UrlCategoryObject] = []
    for it in items:
        try:
            out.append(from_json_dict(it))
        except Exception as exc:
            if strict:
                raise UrlCategoryParseError(f"failed to parse url-category json: {exc}") from exc
    return out
