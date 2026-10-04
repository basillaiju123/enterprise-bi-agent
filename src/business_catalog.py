BUSINESS_CATALOG = [
    {
        "term": "Revenue",
        "definition": (
            "Revenue is calculated as the sum of order item quantity "
            "multiplied by the corresponding product price."
        ),
        "sql_logic": (
            "SUM(order_items.quantity * products.price)"
        ),
    },
    {
        "term": "Completed Order",
        "definition": (
            "An order is considered completed when orders.status "
            "is equal to 'Completed'."
        ),
        "sql_logic": (
            "orders.status = 'Completed'"
        ),
    },
    {
        "term": "Cancelled Order",
        "definition": (
            "An order is considered cancelled when orders.status "
            "is equal to 'Cancelled'."
        ),
        "sql_logic": (
            "orders.status = 'Cancelled'"
        ),
    },
    {
        "term": "Order Quantity",
        "definition": (
            "Order quantity represents the number of units purchased "
            "from an order item."
        ),
        "sql_logic": (
            "SUM(order_items.quantity)"
        ),
    },
    {
        "term": "Average Order Value",
        "definition": (
            "Average Order Value is the total revenue divided by "
            "the number of completed orders."
        ),
        "sql_logic": (
            "SUM(order_items.quantity * products.price) "
            "/ COUNT(DISTINCT orders.order_id)"
        ),
    },
]