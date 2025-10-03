# src/optiv_lib/providers/pan/objects/url_category/serializer.py
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Iterable, List

import xmltodict

from .model import UrlCategoryObject


def parent_xpath(device_group: str | None) -> str:
    """Shared or device-group container XPath for custom URL categories."""
    if device_group is None:
        return "/config/shared/profiles/custom-url-category"
    return f"/config/devices/entry/device-group/entry[@name='{device_group}']/profiles/custom-url-category"


def entry_xpath(name: str, device_group: str | None) -> str:
    """XPath for a specific custom URL category entry."""
    return f"{parent_xpath(device_group)}/entry[@name='{name}']"


# ----------------------------
# XML serialization
# ----------------------------

def to_xml(obj: UrlCategoryObject) -> str:
    """
    Serialize UrlCategoryObject to a PAN-OS <entry> XML fragment.

    Layout:
      <entry name="...">
        <list><member>...</member>...</list>
        <type>URL List|Category Match</type>
        <description>...</description>
      </entry>
    """
    entry: Dict[str, Any] = OrderedDict()
    entry["@name"] = obj.name
    members = list(obj.urls if obj.type == "URL List" else obj.categories)
    entry["list"] = {"member": members}
    entry["type"] = obj.type
    if obj.description:
        entry["description"] = obj.description
    return xmltodict.unparse({"entry": entry}, full_document=False)


def to_xml_list(objs: Iterable[UrlCategoryObject]) -> List[str]:
    """Serialize many UrlCategoryObject items to a list of <entry> XML strings."""
    return [to_xml(o) for o in objs]


# ----------------------------
# JSON serialization
# ----------------------------

def to_json_dict(obj: UrlCategoryObject) -> Dict[str, Any]:
    """Serialize to a compact JSON-ready dict."""
    d: Dict[str, Any] = {
        "name": obj.name,
        "type": obj.type,
    }
    if obj.type == "URL List":
        d["urls"] = list(obj.urls)
    else:
        d["categories"] = list(obj.categories)
    if obj.description:
        d["description"] = obj.description
    return d


def to_json_list(objs: Iterable[UrlCategoryObject]) -> List[Dict[str, Any]]:
    """Serialize many to JSON-ready dicts."""
    return [to_json_dict(o) for o in objs]


def to_json(obj: UrlCategoryObject, *, indent: int = 2) -> str:
    """Serialize one object to a JSON string."""
    import json
    return json.dumps(to_json_dict(obj), indent=indent, ensure_ascii=False)
