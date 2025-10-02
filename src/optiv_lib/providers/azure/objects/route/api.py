# src/optiv_lib/providers/azure/objects/route/api.py
from __future__ import annotations

from typing import List

from azure.mgmt.core.tools import parse_resource_id
from azure.mgmt.network.models import Route

from optiv_lib.providers.azure.clients import network_client
from optiv_lib.providers.azure.objects.route_table import api as rt_api
from optiv_lib.providers.azure.threads import thread_map_flat


def list_routes(subscription_id: str, resource_group: str, route_table_name: str) -> List[Route]:
    """List routes within a specific route table."""
    net = network_client(subscription_id)
    return list(net.routes.list(resource_group_name=resource_group, route_table_name=route_table_name))


def get_route(subscription_id: str, resource_group: str, route_table_name: str, route_name: str) -> Route:
    """Get a specific route."""
    net = network_client(subscription_id)
    return net.routes.get(
        resource_group_name=resource_group,
        route_table_name=route_table_name,
        route_name=route_name,
    )


def get_route_by_id(resource_id: str) -> Route:
    """
    Get a route by full resource ID:
    /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/routeTables/<rt>/routes/<route>
    """
    rid = parse_resource_id(resource_id)
    sub_id = rid["subscription"]
    rg = rid["resource_group"]
    rt_name, route_name = rid["name"].split("/routes/", 1)
    net = network_client(sub_id)
    return net.routes.get(resource_group_name=rg, route_table_name=rt_name, route_name=route_name)


def list_all_routes(max_workers: int | None = None) -> List[Route]:
    """
    Across all subscriptions: reuse route_table/api.py to enumerate all route tables,
    then list routes per route table in threads.
    """
    route_tables = rt_api.list_all_route_tables(max_workers=max_workers)

    def _fetch_routes(rt_obj) -> List[Route]:
        rid = parse_resource_id(rt_obj.id)  # RouteTable.id
        sub_id = rid["subscription"]
        rg = rid["resource_group"]
        rt_name = rid["resource_name"]
        net = network_client(sub_id)
        return list(net.routes.list(resource_group_name=rg, route_table_name=rt_name))

    return thread_map_flat(_fetch_routes, route_tables, max_workers=max_workers, ignore_errors=True)
