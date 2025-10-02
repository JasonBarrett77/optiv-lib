# src/optiv_lib/providers/azure/objects/public_ip/api.py
from __future__ import annotations

from typing import List

from azure.mgmt.core.tools import parse_resource_id
from azure.mgmt.network.models import PublicIPAddress

from optiv_lib.providers.azure.clients import network_client


def list_public_ips(subscription_id: str) -> List[PublicIPAddress]:
    """
    List all Public IP addresses in the subscription.
    """
    client = network_client(subscription_id)
    return list(client.public_ip_addresses.list_all())


def list_public_ips_in_rg(subscription_id: str, resource_group: str) -> List[PublicIPAddress]:
    """
    List Public IP addresses in a specific resource group.
    """
    client = network_client(subscription_id)
    return list(client.public_ip_addresses.list(resource_group_name=resource_group))


def get_public_ip(subscription_id: str, resource_group: str, name: str) -> PublicIPAddress:
    """
    Get a specific Public IP address by name.
    """
    client = network_client(subscription_id)
    return client.public_ip_addresses.get(resource_group_name=resource_group, public_ip_address_name=name)


def get_public_ip_by_id(resource_id: str) -> PublicIPAddress:
    """
    Retrieve a Public IP object directly by its Azure resource ID.

    Args:
        resource_id: Full Azure resource ID for the public IP address.

    Returns:
        PublicIPAddress object.
    """
    id_parts = parse_resource_id(resource_id)
    client = network_client(subscription_id=id_parts.get('subscription'))
    return client.public_ip_addresses.get(resource_group_name=id_parts.get('resource_group'), public_ip_address_name=id_parts.get('name'))