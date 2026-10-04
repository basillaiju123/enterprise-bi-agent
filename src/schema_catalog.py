SCHEMA_CATALOG = [
    {
        "table": "customers",
        "description": "Contains customer information.",
        "columns": {
            "customer_id": "Unique identifier for each customer.",
            "customer_name": "Customer's name.",
            "country": "Country where the customer is located.",
            "signup_date": "Date when the customer signed up."
        }
    },
    {
        "table": "products",
        "description": "Contains product information.",
        "columns": {
            "product_id": "Unique identifier for each product.",
            "product_name": "Name of the product.",
            "category": "Product category.",
            "price": "Product price."
        }
    },
    {
        "table": "orders",
        "description": "Contains customer orders.",
        "columns": {
            "order_id": "Unique identifier for each order.",
            "customer_id": "Customer who placed the order.",
            "order_date": "Date when the order was placed.",
            "status": "Order status such as Completed or Cancelled."
        }
    },
    {
        "table": "order_items",
        "description": "Contains the products included in each order.",
        "columns": {
            "order_id": "Order associated with the item.",
            "product_id": "Product included in the order.",
            "quantity": "Number of units of the product purchased."
        }
    }
]