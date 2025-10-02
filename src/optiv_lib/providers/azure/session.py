# src/optiv_lib/providers/azure/session.py
from __future__ import annotations

import base64
import json
import threading
from dataclasses import dataclass
from typing import Optional

from azure.core.credentials import TokenCredential
from azure.identity import (InteractiveBrowserCredential, TokenCachePersistenceOptions, )
from azure.mgmt.resource.subscriptions import SubscriptionClient

__all__ = ["AzureSession", "create_azure_session", "get_session", "clear_session_cache"]

ARM_SCOPE = "https://management.azure.com/.default"
MSA_CONSUMERS_TENANT = "9188040d-6c67-4c5b-b112-36a304b66dad"

_SESSION_LOCK = threading.Lock()
_SESSION: Optional["AzureSession"] = None


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def _jwt_tid(access_token: str) -> Optional[str]:
    try:
        _header, payload, _sig = access_token.split(".")
        data = json.loads(_b64url_decode(payload))
        tid = data.get("tid")
        if isinstance(tid, str):
            return tid
    except Exception:
        pass
    return None


@dataclass(slots=True)
class AzureSession:
    credential: InteractiveBrowserCredential | TokenCredential
    tenant_id: str

    def subscriptions_client(self) -> SubscriptionClient:
        return SubscriptionClient(credential=self.credential)

    def list_subscriptions(self) -> list[tuple[str, str]]:
        client = self.subscriptions_client()
        return [(s.subscription_id, s.display_name) for s in client.subscriptions.list()]

    def list_tenants(self) -> list[str]:
        client = self.subscriptions_client()
        return [t.tenant_id for t in client.tenants.list()]


def create_azure_session(preferred_tenant: Optional[str] = None, *, use_persistent_cache: bool = True, allow_unencrypted_cache: bool = False, ) -> AzureSession:
    cache_opts = TokenCachePersistenceOptions(enabled=use_persistent_cache, allow_unencrypted_storage=allow_unencrypted_cache, name="azure_identity_tokens", )

    # Acquire ONE token to discover tenant
    base_cred = InteractiveBrowserCredential(tenant_id=preferred_tenant or "organizations", token_cache_persistence_options=cache_opts, additionally_allowed_tenants=["*"], )
    token = base_cred.get_token(ARM_SCOPE)  # single prompt happens here
    tid = _jwt_tid(token.token) or ""

    if tid == MSA_CONSUMERS_TENANT:
        # Pick a real AAD tenant, but keep using base_cred
        tenants = [t.tenant_id for t in SubscriptionClient(credential=base_cred).tenants.list()]
        candidates = [t for t in tenants if t and t.lower() != MSA_CONSUMERS_TENANT]
        if preferred_tenant and preferred_tenant not in candidates:
            raise RuntimeError(f"Preferred tenant {preferred_tenant} not found among available AAD tenants: {candidates!r}")
        final_tenant = preferred_tenant or (candidates[0] if candidates else "")
        if not final_tenant:
            raise RuntimeError("No Azure AD tenant linked to this Microsoft account.")
        # Return the original credential; DO NOT create a new one
        return AzureSession(credential=base_cred, tenant_id=final_tenant)

    # Non-consumers path: reuse base_cred and discovered tenant
    final_tenant = tid or (preferred_tenant or "organizations")
    return AzureSession(credential=base_cred, tenant_id=final_tenant)


def get_session() -> AzureSession:
    """
    Return a cached AzureSession. Creates it on first use via interactive login.
    Single-tenant assumption: no tenant switching.
    """
    global _SESSION
    if _SESSION is None:
        with _SESSION_LOCK:
            if _SESSION is None:
                _SESSION = create_azure_session()
    return _SESSION


def clear_session_cache() -> None:
    """Clear the cached AzureSession (e.g., after credential/tenant change)."""
    global _SESSION
    with _SESSION_LOCK:
        _SESSION = None
