# src/optiv_lib/providers/pan/objects/address/api.py
from __future__ import annotations

from typing import List, Optional

from optiv_lib.providers.pan import ops
from optiv_lib.providers.pan.objects.address.model import AddressObject, ConfigSource
from optiv_lib.providers.pan.objects.address.parser import parse_addresses
from optiv_lib.providers.pan.objects.address.serializer import entry_xpath, parent_xpath, render_entry
from optiv_lib.providers.pan.session import PanoramaSession


def list_addresses(*, session: PanoramaSession, candidate: bool = True, device_group: Optional[str] = None, ) -> List[AddressObject]:
    """
    List address objects from candidate or running config.
    """
    xpath = parent_xpath(device_group)
    if candidate:
        result = ops.config_get(session=session, xpath=xpath)
        config_source: ConfigSource = "candidate"
    else:
        result = ops.config_show(session=session, xpath=xpath)
        config_source = "running"
    return parse_addresses(result, source=config_source, device_group=device_group, strict=True)


def create_address(address_object: AddressObject, *, session: PanoramaSession) -> dict:
    """
    Create (or merge) an address entry under the correct scope.
    """
    xpath = parent_xpath(address_object.device_group)
    element = render_entry(address_object)
    return ops.config_set(session=session, xpath=xpath, element=element)


def update_address(address_object: AddressObject, *, session: PanoramaSession) -> dict:
    """
    Replace an existing address entry in place.
    """
    xpath = entry_xpath(address_object.name, address_object.device_group)
    element = render_entry(address_object)
    return ops.config_edit(session=session, xpath=xpath, element=element)


def rename_address(*, old_name: str, new_name: str, device_group: Optional[str], session: PanoramaSession, ) -> dict:
    """
    Rename an existing address entry.
    """
    xpath = entry_xpath(old_name, device_group)
    return ops.config_rename(session=session, xpath=xpath, newname=new_name)


def delete_address(*, name: str, device_group: Optional[str], session: PanoramaSession, ) -> dict:
    """
    Delete an address entry.
    """
    xpath = entry_xpath(name, device_group)
    return ops.config_delete(session=session, xpath=xpath)
