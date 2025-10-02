# src/optiv_lib/providers/azure/clients.py
from __future__ import annotations

from typing import Dict, Optional

from azure.core.pipeline.transport import RequestsTransport
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient

from .session import clear_session_cache, get_session


__all__ = [
    "subscription_client",
    "network_client",
    "compute_client",
    "resource_client",
    "clear_client_cache",
    "clear_session_cache",
    "close_all",
]

from .threads import shutdown_threads

# Shared HTTP transport and UA across clients
USER_AGENT = "optiv-lib/0.99.1 (+https://github.com/JasonBarrett77/optiv-lib)"
_TRANSPORT = RequestsTransport(connection_timeout=10, read_timeout=60, connection_pool_maxsize=32)

# Module-level caches
_SUBSCRIPTION_CLIENT: Optional[SubscriptionClient] = None
_NETWORK_CLIENTS: Dict[str, NetworkManagementClient] = {}
_COMPUTE_CLIENTS: Dict[str, ComputeManagementClient] = {}
_RESOURCE_CLIENTS: Dict[str, ResourceManagementClient] = {}


def subscription_client() -> SubscriptionClient:
    """Cached SubscriptionClient. Single tenant → one per process."""
    global _SUBSCRIPTION_CLIENT
    if _SUBSCRIPTION_CLIENT is None:
        _SUBSCRIPTION_CLIENT = SubscriptionClient(
            credential=get_session().credential,
            transport=_TRANSPORT,
            user_agent=USER_AGENT,
        )
    return _SUBSCRIPTION_CLIENT


def network_client(subscription_id: str) -> NetworkManagementClient:
    """Cached NetworkManagementClient per subscription."""
    client = _NETWORK_CLIENTS.get(subscription_id)
    if client is None:
        client = NetworkManagementClient(
            credential=get_session().credential,
            subscription_id=subscription_id,
            transport=_TRANSPORT,
            user_agent=USER_AGENT,
        )
        _NETWORK_CLIENTS[subscription_id] = client
    return client


def compute_client(subscription_id: str) -> ComputeManagementClient:
    """Cached ComputeManagementClient per subscription."""
    client = _COMPUTE_CLIENTS.get(subscription_id)
    if client is None:
        client = ComputeManagementClient(
            credential=get_session().credential,
            subscription_id=subscription_id,
            transport=_TRANSPORT,
            user_agent=USER_AGENT,
        )
        _COMPUTE_CLIENTS[subscription_id] = client
    return client


def resource_client(subscription_id: str) -> ResourceManagementClient:
    """Cached ResourceManagementClient per subscription."""
    client = _RESOURCE_CLIENTS.get(subscription_id)
    if client is None:
        client = ResourceManagementClient(
            credential=get_session().credential,
            subscription_id=subscription_id,
            transport=_TRANSPORT,
            user_agent=USER_AGENT,
        )
        _RESOURCE_CLIENTS[subscription_id] = client
    return client


def clear_client_cache() -> None:
    """Clear all client caches. Call if session/credential changes."""
    global _SUBSCRIPTION_CLIENT
    _SUBSCRIPTION_CLIENT = None
    _NETWORK_CLIENTS.clear()
    _COMPUTE_CLIENTS.clear()
    _RESOURCE_CLIENTS.clear()


def close_all() -> None:
    """
    Close down client caches and background threads.
    Intended for teardown or when rotating credentials/tenants.
    """
    clear_client_cache()
    shutdown_threads(wait=True)
    clear_session_cache()
