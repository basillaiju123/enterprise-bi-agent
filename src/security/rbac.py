ROLE_PERMISSIONS = {
    "admin": {
        "allowed_tables": {
            "customers",
            "products",
            "orders",
            "order_items",
        }
    },
    "analyst": {
        "allowed_tables": {
            "customers",
            "products",
            "orders",
            "order_items",
        }
    },
    "viewer": {
        "allowed_tables": {
            "customers",
            "products",
        }
    },
}


def get_allowed_tables(role: str) -> set[str]:
    permissions = ROLE_PERMISSIONS.get(role)

    if permissions is None:
        raise ValueError(f"Unknown role: {role}")

    return permissions["allowed_tables"]


def is_table_allowed(role: str, table_name: str) -> bool:
    return table_name.lower() in get_allowed_tables(role)


def validate_role(role: str) -> bool:
    return role in ROLE_PERMISSIONS
