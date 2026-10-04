SQL_EXAMPLES = [
    {
        "id": "sql_example_customers_india",
        "question": "How many customers are from India?",
        "sql": """
SELECT COUNT(*)
FROM customers
WHERE country = 'India';
""",
        "description": "Count customers filtered by country."
    },
    {
        "id": "sql_example_electronics_products",
        "question": "What products are in the Electronics category?",
        "sql": """
SELECT product_id, product_name
FROM products
WHERE category = 'Electronics';
""",
        "description": "List products filtered by category."
    },
    {
        "id": "sql_example_most_expensive",
        "question": "What is the most expensive product?",
        "sql": """
SELECT product_name, price
FROM products
ORDER BY price DESC
LIMIT 1;
""",
        "description": "Find the product with the highest price."
    },
    {
        "id": "sql_example_completed_orders",
        "question": "How many orders were completed?",
        "sql": """
SELECT COUNT(*)
FROM orders
WHERE status = 'Completed';
""",
        "description": "Count orders using the completed status."
    },
    {
        "id": "sql_example_india_completed_orders",
        "question": "How many orders were completed by customers from India?",
        "sql": """
SELECT COUNT(DISTINCT orders.order_id)
FROM orders
JOIN customers
    ON orders.customer_id = customers.customer_id
WHERE orders.status = 'Completed'
  AND customers.country = 'India';
""",
        "description": "Count completed orders for customers from a specific country."
    },
    {
        "id": "sql_example_revenue",
        "question": "What is the revenue?",
        "sql": """
SELECT SUM(order_items.quantity * products.price) AS revenue
FROM order_items
JOIN products
    ON order_items.product_id = products.product_id;
""",
        "description": "Calculate revenue from order item quantities and product prices."
    }
]
