BUSINESS_CATALOG = [
    {
        "term": "Revenue",
        "definition": (
            "Revenue is the sum of each order item's quantity multiplied "
            "by the corresponding product price. Join order_items to "
            "products on product_id. When filtering by order status, join "
            "orders to order_items on order_id."
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
        "sql_logic": "orders.status = 'Completed'",
    },
    {
        "term": "Cancelled Order",
        "definition": (
            "An order is considered cancelled when orders.status "
            "is equal to 'Cancelled'."
        ),
        "sql_logic": "orders.status = 'Cancelled'",
    },
    {
        "term": "Order Quantity",
        "definition": (
            "Order quantity represents the number of units purchased "
            "from an order item. It is not revenue."
        ),
        "sql_logic": "SUM(order_items.quantity)",
    },
    {
        "term": "Average Order Value",
        "definition": (
            "Average Order Value is completed-order revenue divided by "
            "the number of distinct completed orders."
        ),
        "sql_logic": (
            "SUM(order_items.quantity * products.price) "
            "/ COUNT(DISTINCT orders.order_id)"
        ),
    },
    {
        "term": "Country Name Aliases",
        "definition": (
            "In this sample warehouse, the customers.country value 'UK' "
            "represents the United Kingdom. Filter using the stored value "
            "'UK' when the question says United Kingdom."
        ),
        "sql_logic": "customers.country = 'UK'",
    },
]
