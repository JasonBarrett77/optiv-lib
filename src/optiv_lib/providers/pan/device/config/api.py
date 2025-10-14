# src/optiv_lib/providers/pan/device/config/api.py
from __future__ import annotations

from optiv_lib.providers.pan.ops import config_get_on_device, config_show_on_device, op_on_device
from optiv_lib.providers.pan.session import PanoramaSession


def get_effective_running_config(*, session: PanoramaSession, device_serial: str, ) -> dict:
    """
    Full effective running config (merged templates + local) via Panorama proxy.
    Equivalent to device CLI: show config running
    Returns inner 'result'.
    """
    cmd = "<show><config><running/></config></show>"
    return op_on_device(session=session, cmd=cmd, target=device_serial)


def get_running_node(*, session: PanoramaSession, device_serial: str, xpath: str, ) -> dict:
    """
    Running config subtree at XPath on the device via Panorama proxy.
    """
    return config_show_on_device(session=session, xpath=xpath, target=device_serial)


def get_candidate_node(*, session: PanoramaSession, device_serial: str, xpath: str, ) -> dict:
    """
    Candidate config subtree at XPath on the device via Panorama proxy.
    """
    return config_get_on_device(session=session, xpath=xpath, target=device_serial)
