# src/optiv_lib/providers/pan/session.py
from __future__ import annotations

import ssl
from typing import Union

import requests
import truststore
import xmltodict
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

try:
    truststore.inject_into_ssl()
except Exception:
    pass

VerifyType = Union[bool, str]  # bool or CA bundle path


class PanoramaAuthError(RuntimeError):
    """Auth or key generation failure."""


class PanoramaHTTPError(RuntimeError):
    """HTTP error talking to Panorama."""


class _NoVerifyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        pool_kwargs["ssl_context"] = ctx
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        proxy_kwargs["ssl_context"] = ctx
        return super().proxy_manager_for(proxy, **proxy_kwargs)


def _redact(text: str, secret: str) -> str:
    try:
        if not secret:
            return text
        variants = [secret]
        try:
            from urllib.parse import quote, quote_plus
            variants += [quote(secret, safe=""), quote_plus(secret)]
        except Exception:
            pass
        for v in {v for v in variants if v}:
            text = text.replace(v, "******")
        return text
    except Exception:
        return "[REDACTED]"


def _api_key(base_url, username, password, verify, timeout) -> str:
    try:
        r = requests.request(method="POST", url=base_url, params={"type": "keygen", "user": username, "password": password}, verify=verify, timeout=timeout, )
        r.raise_for_status()
    except requests.RequestException as e:
        msg = f"Panorama connection error: {_redact(str(e), password)}"
        del password
        raise PanoramaHTTPError(msg) from None
    del password
    try:
        data = xmltodict.parse(r.text)
        key = data.get("response", {}).get("result", {}).get("key")
    except Exception as e:
        raise PanoramaAuthError("Keygen parse error.") from e

    if not key:
        raise PanoramaAuthError("Failed to retrieve API key.")
    return key


class PanoramaSession(requests.Session):
    """
    Thin requests.Session for Panorama XML API.

    - Builds API key on init (type=keygen).
    - Injects ?key=... into every request.
    - Respects verify: bool or CA bundle path.
    """

    def __init__(self, *, hostname: str, username: str, password: str, verify: VerifyType = True, timeout: float = 15.0, ):
        super().__init__()
        self.base_url = f"https://{hostname}/api/"
        self.timeout = timeout
        self.verify = verify

        if verify is False:
            adapter = _NoVerifyAdapter()
            self.mount("https://", adapter)
            self.mount("http://", adapter)

        self.api_key = _api_key(base_url=self.base_url, username=username, password=password, verify=self.verify, timeout=self.timeout, )
        del password

    def request(self, method: str, url: str, **kwargs):
        full_url = url if url.startswith("http") else (self.base_url + url.lstrip("/"))
        params = kwargs.pop("params", {}) or {}
        params.setdefault("key", self.api_key)
        kwargs["params"] = params
        kwargs.setdefault("timeout", self.timeout)
        return super().request(method, full_url, **kwargs)
