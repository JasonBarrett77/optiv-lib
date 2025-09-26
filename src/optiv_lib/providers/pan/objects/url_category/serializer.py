# src/optiv_lib/providers/pan/objects/url_category/serializer.py
from __future__ import annotations

from collections import OrderedDict
import xmltodict

from optiv_lib.providers.pan.objects.url_category.model import UrlCategoryObject


def parent_xpath(device_group: str | None) -> str:
    """
    Shared or device-group container XPath for custom URL categories.
    """
    if device_group is None:
        return "/config/shared/profiles/custom-url-category"
    return f"/config/devices/entry/device-group/entry[@name='{device_group}']/profiles/custom-url-category"


def entry_xpath(name: str, device_group: str | None) -> str:
    """
    XPath for a specific custom URL category entry.
    """
    return f"{parent_xpath(device_group)}/entry[@name='{name}']"


def render_entry(obj: UrlCategoryObject) -> str:
    """
    Serialize UrlCategoryObject to a single <entry> element using xmltodict.unparse.

    Layout:
      <entry name="...">
        <list><member>...</member>...</list>
        <type>URL List|Category Match</type>
        <description>...</description>
      </entry>
    """
    entry = OrderedDict()
    entry["@name"] = obj.name

    members = list(obj.urls if obj.type == "URL List" else obj.categories)
    entry["list"] = {"member": members}

    entry["type"] = obj.type
    if obj.description:
        entry["description"] = obj.description

    return xmltodict.unparse({"entry": entry}, full_document=False)
