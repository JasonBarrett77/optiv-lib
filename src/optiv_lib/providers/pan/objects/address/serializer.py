# src/optiv_lib/providers/pan/objects/address/serializer.py
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Iterable, List

import xmltodict

from .model import AddressObject


def parent_xpath(device_group: str | None) -> str:
    """Shared or device-group container XPath for addresses."""
    if device_group is None:
        return "/config/shared/address"
    return f"/config/devices/entry/device-group/entry[@name='{device_group}']/address"


def entry_xpath(name: str, device_group: str | None) -> str:
    """XPath for a specific address entry."""
    return f"{parent_xpath(device_group)}/entry[@name='{name}']"


# ----------------------------
# XML serialization
# ----------------------------

def to_xml(obj: AddressObject) -> str:
    """
    Serialize AddressObject to a PAN-OS <entry> XML fragment.

    Layout:
      <entry name="...">
        <ip-netmask>...</ip-netmask> | <fqdn>...</fqdn> | etc.
        <description>...</description>
        <tag><member>...</member>...</tag>
        <disable-override>yes</disable-override>
      </entry>
    """
    entry: Dict[str, Any] = OrderedDict()
    entry["@name"] = obj.name
    entry[obj.kind] = obj.value
    if obj.description:
        entry["description"] = obj.description
    if obj.tags:
        entry["tag"] = {"member": list(obj.tags)}
    if obj.disable_override:
        entry["disable-override"] = "yes"

    return xmltodict.unparse({"entry": entry}, full_document=False)


def to_xml_list(objs: Iterable[AddressObject]) -> List[str]:
    """Serialize many AddressObject items to a list of <entry> XML strings."""
    return [to_xml(o) for o in objs]


# ----------------------------
# JSON serialization
# ----------------------------

def to_json_dict(obj: AddressObject) -> Dict[str, Any]:
    """Serialize to a compact JSON-ready dict."""
    d: Dict[str, Any] = {
        "name": obj.name,
        "kind": obj.kind,
        "value": obj.value,
    }
    if obj.description:
        d["description"] = obj.description
    if obj.tags:
        d["tags"] = list(obj.tags)
    if obj.disable_override:
        d["disable_override"] = True
    return d


def to_json_list(objs: Iterable[AddressObject]) -> List[Dict[str, Any]]:
    """Serialize many to JSON-ready dicts."""
    return [to_json_dict(o) for o in objs]


def to_json(obj: AddressObject, *, indent: int = 2) -> str:
    """Serialize one object to a JSON string."""
    import json
    return json.dumps(to_json_dict(obj), indent=indent, ensure_ascii=False)
