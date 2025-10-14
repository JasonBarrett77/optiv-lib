# src/optiv_lib/providers/pan/panorama/managed_devices/api.py
from __future__ import annotations

from optiv_lib.providers.pan import ops
from optiv_lib.providers.pan.session import PanoramaSession


def list_connected(*, session: PanoramaSession) -> dict:
    """
    Panorama → show devices connected
    Returns inner 'result'.
    """
    cmd = "<show><devices><connected/></devices></show>"
    return ops.op(session=session, cmd=cmd)


def list_all(*, session: PanoramaSession) -> dict:
    """
    Panorama → show devices all
    Returns inner 'result'.
    """
    cmd = "<show><devices><all/></devices></show>"
    return ops.op(session=session, cmd=cmd)
