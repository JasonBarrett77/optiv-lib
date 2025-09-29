# src/optiv_lib/providers/pan/session.py
from __future__ import annotations

import ssl
from typing import Callable, Union, overload

import requests
import truststore
import xmltodict
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from optiv_lib.config import AppConfig, PanoramaConfig

try:
    truststore.inject_into_ssl()
except Exception:
    pass

VerifyType = Union[bool, str]


class PanoramaAuthError(RuntimeError):
    """Authentication/keygen failure when obtaining or validating the API key."""


class PanoramaHTTPError(RuntimeError):
    """HTTP or API-layer error returned while talking to Panorama."""


class PanoramaTimeoutError(PanoramaHTTPError):
    """Request timed out (after retries) while communicating with Panorama."""


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


def _api_key(*, base_url: str, username: str, password_get: Callable[[], str], verify: VerifyType, timeout: float) -> str:
    pwd = password_get()
    try:
        r = requests.request("POST", base_url, params={"type": "keygen", "user": username, "password": pwd}, verify=verify, timeout=timeout, )
        r.raise_for_status()
    except requests.RequestException as e:
        raise PanoramaHTTPError(f"Panorama connection error: {_redact(str(e), pwd)}") from None
    finally:
        pwd = ""

    try:
        data = xmltodict.parse(r.text)
        key = data.get("response", {}).get("result", {}).get("key")
    except Exception as e:
        raise PanoramaAuthError("Keygen parse error.") from e
    if not key:
        raise PanoramaAuthError("Failed to retrieve API key.")
    return key


def _require_pano_cfg(obj: PanoramaConfig | AppConfig) -> PanoramaConfig:
    if isinstance(obj, PanoramaConfig):
        return obj
    if isinstance(obj, AppConfig) and obj.panorama:
        return obj.panorama
    raise ValueError("PanoramaConfig is required. Pass a PanoramaConfig or an AppConfig with .panorama populated.")


class PanoramaSession(requests.Session):
    """
    Thin requests.Session for Panorama XML API.

    Accepts either:
      - PanoramaConfig
      - AppConfig (must have .panorama)

    Raises ValueError if config is missing.
    """

    @overload
    def __init__(self, cfg: PanoramaConfig):
        ...

    @overload
    def __init__(self, cfg: AppConfig):
        ...

    def __init__(self, cfg: PanoramaConfig | AppConfig):
        super().__init__()
        pano = _require_pano_cfg(cfg)

        self.base_url = f"https://{pano.hostname}/api/"
        self.timeout = pano.timeout
        self.verify = pano.verify

        if pano.verify is False:
            adapter = _NoVerifyAdapter()
            self.mount("https://", adapter)
            self.mount("http://", adapter)

        self.api_key = _api_key(base_url=self.base_url, username=pano.username, password_get=pano.password.get, verify=self.verify, timeout=self.timeout, )

    def request(self, method: str, url: str, **kwargs):
        full_url = url if url.startswith("http") else (self.base_url + url.lstrip("/"))
        params = kwargs.pop("params", {}) or {}
        params.setdefault("key", self.api_key)
        kwargs["params"] = params
        kwargs.setdefault("timeout", self.timeout)
        return super().request(method, full_url, **kwargs)
