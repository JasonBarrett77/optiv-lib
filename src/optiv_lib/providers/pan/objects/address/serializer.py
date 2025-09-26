from __future__ import annotations

from collections import OrderedDict

import xmltodict
from optiv_lib.providers.pan.objects.address.model import AddressObject


def parent_xpath(device_group: str | None) -> str:
    """Return the shared or device-group container XPath for addresses."""
    if device_group is None:
        return "/config/shared/address"
    return f"/config/devices/entry/device-group/entry[@name='{device_group}']/address"


def entry_xpath(name: str, device_group: str | None) -> str:
    """Return the XPath for a specific address entry."""
    return f"{parent_xpath(device_group)}/entry[@name='{name}']"


def render_entry(obj: AddressObject) -> str:
    """
    Serialize AddressObject to a single <entry> element using xmltodict.unparse.

    Child order: value → description → tag → disable-override.
    """
    entry = OrderedDict()
    entry["@name"] = obj.name
    entry[obj.kind] = obj.value
    if obj.description:
        entry["description"] = obj.description
    if obj.tags:
        entry["tag"] = {"member": list(obj.tags)}
    if obj.disable_override:
        entry["disable-override"] = "yes"

    return xmltodict.unparse({"entry": entry}, full_document=False)
