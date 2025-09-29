from __future__ import annotations

# Re-export object APIs at provider level
from .objects.address.api import (
    list_addresses,
    create_address,
    update_address,
    rename_address,
    delete_address,
)
from .objects.url_category.api import (
    list_predefined_url_categories,
    list_url_categories,
    create_url_category,
    update_url_category,
    rename_url_category,
    delete_url_category,
)

__all__ = [

    # Address APIs
    "list_addresses",
    "create_address",
    "update_address",
    "rename_address",
    "delete_address",

    # URL Category APIs
    "list_predefined_url_categories",
    "list_url_categories",
    "create_url_category",
    "update_url_category",
    "rename_url_category",
    "delete_url_category",
]
