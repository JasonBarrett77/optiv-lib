# src/optiv_lib/providers/azure/objects/subnet/api.py
from __future__ import annotations

from typing import List

from azure.mgmt.core.tools import parse_resource_id
from azure.mgmt.network.models import Subnet

from optiv_lib.providers.azure.clients import network_client
from optiv_lib.providers.azure.objects.subscription.api import list_subscriptions
from optiv_lib.providers.azure.threads import thread_map_flat


def list_subnets(subscription_id: str, resource_group: str, vnet_name: str) -> List[Subnet]:
    """
    List all subnets in a virtual network.
    """
    client = network_client(subscription_id)
    return list(client.subnets.list(resource_group_name=resource_group, virtual_network_name=vnet_name))


def get_subnet(subscription_id: str, resource_group: str, vnet_name: str, subnet_name: str) -> Subnet:
    """
    Get a specific subnet by name.
    """
    client = network_client(subscription_id)
    return client.subnets.get(
        resource_group_name=resource_group,
        virtual_network_name=vnet_name,
        subnet_name=subnet_name,
    )


def get_subnet_by_id(resource_id: str) -> Subnet:
    """
    Get a subnet by its full resource ID.
    """
    rid = parse_resource_id(resource_id)
    client = network_client(subscription_id=rid["subscription"])
    return client.subnets.get(
        resource_group_name=rid["resource_group"],
        virtual_network_name=rid["name"],
        subnet_name=rid.get("child_name_1") or rid.get("resource_name"),
    )


def list_all_subnets(max_workers: int | None = None) -> List[Subnet]:
    """
    List all subnets across all accessible subscriptions using threads.
    """
    sub_ids = [s.subscription_id for s in list_subscriptions()]

    def _fetch_subnets(sub_id: str) -> List[Subnet]:
        net = network_client(sub_id)
        out: List[Subnet] = []
        for vnet in net.virtual_networks.list_all():
            vrid = parse_resource_id(vnet.id)
            rg = vrid["resource_group"]
            vnet_name = vrid.get("resource_name") or vrid["name"]
            out.extend(net.subnets.list(resource_group_name=rg, virtual_network_name=vnet_name))
        return out

    return thread_map_flat(_fetch_subnets, sub_ids, max_workers=max_workers, ignore_errors=True)
