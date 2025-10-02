# src/optiv_lib/providers/azure/objects/route_table/api.py
from __future__ import annotations
from typing import List

from azure.mgmt.core.tools import parse_resource_id
from azure.mgmt.network.models import RouteTable

from optiv_lib.providers.azure.clients import network_client
from optiv_lib.providers.azure.objects.subscription.api import list_subscriptions
from optiv_lib.providers.azure.threads import thread_map_flat


def list_route_tables(subscription_id: str) -> List[RouteTable]:
    client = network_client(subscription_id)
    return list(client.route_tables.list_all())


def list_route_tables_in_rg(subscription_id: str, resource_group: str) -> List[RouteTable]:
    client = network_client(subscription_id)
    return list(client.route_tables.list(resource_group_name=resource_group))


def get_route_table(subscription_id: str, resource_group: str, name: str) -> RouteTable:
    client = network_client(subscription_id)
    return client.route_tables.get(resource_group_name=resource_group, route_table_name=name)


def get_route_table_by_id(resource_id: str) -> RouteTable:
    rid = parse_resource_id(resource_id)
    sub_id = rid["subscription"]
    rg = rid["resource_group"]
    name = rid["resource_name"]
    client = network_client(sub_id)
    return client.route_tables.get(resource_group_name=rg, route_table_name=name)


def list_all_route_tables(max_workers: int | None = None) -> List[RouteTable]:
    subs = [s.subscription_id for s in list_subscriptions()]

    def _fetch(sub_id: str) -> List[RouteTable]:
        return list(network_client(sub_id).route_tables.list_all())

    return thread_map_flat(_fetch, subs, max_workers=max_workers, ignore_errors=True)
