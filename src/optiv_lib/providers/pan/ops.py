# src/optiv_lib/providers/pan/ops.py
from __future__ import annotations

from time import sleep
from typing import Any, Dict

import requests

from optiv_lib.providers.pan.session import PanoramaHTTPError, PanoramaSession, PanoramaTimeoutError
from optiv_lib.providers.pan.util import parse_xml


def _check_status(doc: dict) -> None:
    resp = doc.get("response") or {}
    if resp.get("@status") == "success":
        return
    msg = (resp.get("msg", {}) or {}).get("#text") or resp.get("msg") or "PAN-OS XML API error"
    raise PanoramaHTTPError(str(msg))


def _result(doc: dict) -> dict:
    return (doc.get("response") or {}).get("result") or {}


def _call(*, session: PanoramaSession, method: str, params: Dict[str, Any], retries: int = 3, backoff: float = 0.5, ) -> dict:
    m = method.strip().upper()
    if m not in {"GET", "POST"}:
        # Not a transport failure. Fail fast, no retry.
        raise NotImplementedError(f"Unsupported method: {method}")

    for attempt in range(retries + 1):
        try:
            r = session.get("", params=params) if m == "GET" else session.post("", data=params)

            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                status = getattr(e.response, "status_code", None)
                retriable = (status == 429) or (isinstance(status, int) and 500 <= status < 600)
                if retriable and attempt < retries:
                    sleep(backoff * (2 ** attempt))
                    continue
                raise PanoramaHTTPError(f"HTTP {status}: {e}") from None

            doc = parse_xml(r.text)
            _check_status(doc)
            return _result(doc)

        except (requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout) as e:
            # Timeouts: retry, then raise a distinct error
            if attempt < retries:
                sleep(backoff * (2 ** attempt))
                continue
            raise PanoramaTimeoutError(str(e)) from None

        except requests.ConnectionError as e:
            # TCP resets / DNS / connection aborted: retry then surface
            if attempt < retries:
                sleep(backoff * (2 ** attempt))
                continue
            raise PanoramaHTTPError(str(e)) from None

        except requests.RequestException as e:
            # Other client-side errors: do not retry
            raise PanoramaHTTPError(str(e)) from None

    raise PanoramaHTTPError("Request failed after retries.")


# ---------------------------
# Config API (returns response.result)
# ---------------------------

def config_show(*, session: PanoramaSession, xpath: str) -> dict:
    return _call(session=session, method="GET", params={"type": "config", "action": "show", "xpath": xpath})


def config_get(*, session: PanoramaSession, xpath: str) -> dict:
    return _call(session=session, method="GET", params={"type": "config", "action": "get", "xpath": xpath})


def config_set(*, session: PanoramaSession, xpath: str, element: str) -> dict:
    return _call(session=session, method="POST", params={"type": "config", "action": "set", "xpath": xpath, "element": element}, )


def config_edit(*, session: PanoramaSession, xpath: str, element: str) -> dict:
    return _call(session=session, method="POST", params={"type": "config", "action": "edit", "xpath": xpath, "element": element}, )


def config_delete(*, session: PanoramaSession, xpath: str) -> dict:
    return _call(session=session, method="POST", params={"type": "config", "action": "delete", "xpath": xpath})


def config_rename(*, session: PanoramaSession, xpath: str, newname: str) -> dict:
    return _call(session=session, method="POST", params={"type": "config", "action": "rename", "xpath": xpath, "newname": newname}, )


def config_clone(*, session: PanoramaSession, xpath: str, newname: str) -> dict:
    return _call(session=session, method="POST", params={"type": "config", "action": "clone", "xpath": xpath, "newname": newname}, )


def config_move(*, session: PanoramaSession, xpath: str, where: str, dst: str | None = None) -> dict:
    p: Dict[str, Any] = {"type": "config", "action": "move", "xpath": xpath, "where": where}
    if dst:
        p["dst"] = dst
    return _call(session=session, method="POST", params=p)


# ---------------------------
# Operational API (returns response.result)
# ---------------------------

def op(*, session: PanoramaSession, cmd: str) -> dict:
    """
    Example cmd: "<show><config><running><xpath>shared/address</xpath></running></config></show>"
    """
    return _call(session=session, method="GET", params={"type": "op", "cmd": cmd})


# ---------------------------
# Panorama → device proxy ops/config
# ---------------------------

def op_on_device(*, session: "PanoramaSession", cmd: str, target: str, vsys: str | None = None, ) -> dict:
    """
    Run an operational command on a managed firewall via Panorama proxy.
    Returns inner 'result'.
    """
    params: Dict[str, Any] = {"type": "op", "cmd": cmd, "target": target}
    if vsys:
        params["vsys"] = vsys
    return _call(session=session, method="GET", params=params)


def config_show_on_device(*, session: "PanoramaSession", xpath: str, target: str, ) -> dict:
    """
    Fetch RUNNING config node from device via Panorama proxy.
    Returns inner 'result'.
    """
    params: Dict[str, Any] = {
        "type": "config", "action": "show", "xpath": xpath, "target": target,
        }
    return _call(session=session, method="GET", params=params)


def config_get_on_device(*, session: "PanoramaSession", xpath: str, target: str, ) -> dict:
    """
    Fetch CANDIDATE config node from device via Panorama proxy.
    Returns inner 'result'.
    """
    params: Dict[str, Any] = {
        "type": "config", "action": "get", "xpath": xpath, "target": target,
        }
    return _call(session=session, method="GET", params=params)
