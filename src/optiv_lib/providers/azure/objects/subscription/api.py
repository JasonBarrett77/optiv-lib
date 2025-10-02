# src/optiv_lib/providers/azure/objects/subscription/api.py
from typing import List

from azure.mgmt.resource.subscriptions.v2022_12_01.models import Subscription

from optiv_lib.providers.azure.clients import subscription_client


def list_subscriptions() -> List[Subscription]:
    return list(subscription_client().subscriptions.list())
