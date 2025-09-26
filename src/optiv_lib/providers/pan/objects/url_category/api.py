# src/optiv_lib/providers/pan/objects/url_category/api.py
from __future__ import annotations

from typing import List, Optional

from optiv_lib.providers.pan import ops
from optiv_lib.providers.pan.objects.url_category.model import ConfigSource, UrlCategoryObject
from optiv_lib.providers.pan.objects.url_category.parser import parse_url_categories
from optiv_lib.providers.pan.objects.url_category.serializer import entry_xpath, parent_xpath, render_entry
from optiv_lib.providers.pan.session import PanoramaSession


def list_predefined_url_categories(*, session: PanoramaSession) -> List[str]:
    """
    Return sorted predefined PAN-OS URL categories (immutable set from /config/predefined).
    """
    result = ops.config_get(session=session, xpath="/config/predefined/pan-url-categories")
    entries = (result.get("pan-url-categories") or {}).get("entry") or []
    names = [e.get("@name") for e in entries if isinstance(e, dict) and e.get("@name")]
    return sorted(set(names))


def list_url_categories(*, session: PanoramaSession, candidate: bool = True, device_group: Optional[str] = None, ) -> List[UrlCategoryObject]:
    """
    List custom URL categories from candidate or running config.
    """
    xpath = parent_xpath(device_group)
    if candidate:
        result = ops.config_get(session=session, xpath=xpath)
        config_source: ConfigSource = "candidate"
    else:
        result = ops.config_show(session=session, xpath=xpath)
        config_source = "running"
    return parse_url_categories(result, source=config_source, device_group=device_group, strict=True)


def create_url_category(url_category: UrlCategoryObject, *, session: PanoramaSession) -> dict:
    """
    Create (or merge) a custom URL category under the correct scope.
    """
    xpath = parent_xpath(url_category.device_group)
    element = render_entry(url_category)
    return ops.config_set(session=session, xpath=xpath, element=element)


def update_url_category(url_category: UrlCategoryObject, *, session: PanoramaSession) -> dict:
    """
    Replace an existing custom URL category entry in place.
    """
    xpath = entry_xpath(url_category.name, url_category.device_group)
    element = render_entry(url_category)
    return ops.config_edit(session=session, xpath=xpath, element=element)


def rename_url_category(*, old_name: str, new_name: str, device_group: Optional[str], session: PanoramaSession, ) -> dict:
    """
    Rename an existing custom URL category entry.
    """
    xpath = entry_xpath(old_name, device_group)
    return ops.config_rename(session=session, xpath=xpath, newname=new_name)


def delete_url_category(*, name: str, device_group: Optional[str], session: PanoramaSession, ) -> dict:
    """
    Delete a custom URL category entry.
    """
    xpath = entry_xpath(name, device_group)
    return ops.config_delete(session=session, xpath=xpath)
