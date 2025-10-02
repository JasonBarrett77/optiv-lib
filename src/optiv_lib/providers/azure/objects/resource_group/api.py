# src/optiv_lib/providers/azure/objects/resource_group/api.py
from __future__ import annotations

from typing import List

from azure.mgmt.resource.resources.v2025_04_01.models import ResourceGroup

from optiv_lib.providers.azure.clients import resource_client


def list_resource_groups(subscription_id: str) -> List[ResourceGroup]:
    """
    List all resource groups in the given subscription.

    Args:
        subscription_id: Azure subscription GUID.

    Returns:
        List of ResourceGroup objects.
    """
    client = resource_client(subscription_id)
    return list(client.resource_groups.list())


def get_resource_group(subscription_id: str, name: str) -> ResourceGroup:
    """
    Get a specific resource group by name.

    Args:
        subscription_id: Azure subscription GUID.
        name: Name of the resource group.

    Returns:
        ResourceGroup object.
    """
    client = resource_client(subscription_id)
    return client.resource_groups.get(name)
