# src/optiv_lib/providers/azure/objects/application_gateway/api.py
from __future__ import annotations

from typing import Any, List, Optional

from azure.mgmt.core.tools import parse_resource_id
from azure.mgmt.network.models import ApplicationGateway

from optiv_lib.providers.azure.clients import network_client
from optiv_lib.providers.azure.objects.subscription.api import list_subscriptions
from optiv_lib.providers.azure.threads import thread_map_flat


def list_application_gateways(subscription_id: str, resource_group: str) -> List[ApplicationGateway]:
    client = network_client(subscription_id)
    return list(client.application_gateways.list(resource_group_name=resource_group))


def list_all_application_gateways(max_workers: int | None = None) -> List[ApplicationGateway]:
    """
    List all Application Gateways across all accessible subscriptions using a shared thread pool.
    """
    subs = list_subscriptions()
    sub_ids = [s.subscription_id for s in subs]

    def _fetch(sub_id: str) -> List[ApplicationGateway]:
        return list(network_client(sub_id).application_gateways.list_all())

    return thread_map_flat(_fetch, sub_ids, max_workers=max_workers, ignore_errors=True)


def get_application_gateway_by_id(appgw_id: str) -> ApplicationGateway:
    """
    Fetch a single Application Gateway by its full resource ID.
    """
    rid = parse_resource_id(appgw_id)
    sub_id = rid["subscription"]
    rg = rid["resource_group"]
    name = rid["resource_name"]

    client = network_client(sub_id)
    return client.application_gateways.get(resource_group_name=rg, application_gateway_name=name, )


def get_backend_health_by_id(appgw_id: str, timeout: Optional[float] = 35, ) -> Any:
    """
    Call Application Gateway Backend Health and return the resolved result.
    Uses the LRO 'begin_backend_health' API.
    """
    rid = parse_resource_id(appgw_id)
    sub_id = rid["subscription"]
    rg = rid["resource_group"]
    name = rid["resource_name"]

    client = network_client(sub_id)

    poller = client.application_gateways.begin_backend_health(resource_group_name=rg, application_gateway_name=name, expand="All", )
    return poller.result(timeout=timeout)
