from __future__ import annotations

from typing import Any, Dict, List

from optiv_lib.providers.pan.objects.url_category.model import UrlCategoryObject, UrlCategoryType
from optiv_lib.providers.pan.util import as_list, collect_members, node_text


class UrlCategoryParseError(ValueError):
    """Raised when a url-category <entry> cannot be parsed in strict mode."""


def parse_url_categories(result: Dict[str, Any], *, strict: bool = True, ) -> List[UrlCategoryObject]:
    """
    Convert ops.config_show/get result (inner 'result') into UrlCategoryObject items.
    """
    entries = _pick_entries(result)
    objs: List[UrlCategoryObject] = []
    for entry in entries:
        try:
            objs.append(_entry_to_model(entry))
        except Exception as exc:
            if strict:
                raise UrlCategoryParseError(f"failed to parse url-category entry: {exc}") from exc
    return objs


# -----------------
# internal helpers
# -----------------

def _pick_entries(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Accept either:
      result['custom-url-category']['entry']  OR  result['entry']
    """
    cuc = result.get("custom-url-category")
    raw = (cuc.get("entry") if isinstance(cuc, dict) and "entry" in cuc else result.get("entry"))
    return [e for e in as_list(raw) if isinstance(e, dict)]


def _entry_to_model(entry: Dict[str, Any]) -> UrlCategoryObject:
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
