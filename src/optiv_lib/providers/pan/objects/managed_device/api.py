# src/optiv_lib/providers/pan/objects/managed_devices/api.py
from __future__ import annotations

from optiv_lib.providers.pan import ops
from optiv_lib.providers.pan.session import PanoramaSession


def list_managed_devices_connected(*, session: PanoramaSession) -> dict:
    """
    Panorama → show devices connected

    Returns the inner 'result' dict from the XML API.
    Callers handle normalization as needed.
    """
    cmd = "<show><devices><connected/></devices></show>"
    return ops.op(session=session, cmd=cmd)


def list_managed_devices_all(*, session: PanoramaSession) -> dict:
    """
    Panorama → show devices all

    Returns the inner 'result' dict from the XML API.
    """
    cmd = "<show><devices><all/></devices></show>"
    return ops.op(session=session, cmd=cmd)
