
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
        "id": "sql_example_completed_orders_count_alias",
        "question": "Count all orders with Completed status.",
        "sql": """
SELECT COUNT(*) AS completed_orders
FROM orders
WHERE status = 'Completed';
""",
        "description": "Count all orders with Completed status and use completed_orders as the exact output alias."
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
        "id": "sql_example_cancelled_orders_count_alias",
        "question": "How many orders were cancelled?",
        "sql": """
SELECT COUNT(*) AS cancelled_orders
FROM orders
WHERE status = 'Cancelled';
""",
        "description": "Count orders with Cancelled status and use cancelled_orders as the exact output alias."
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
    },
    {
        "id": "sql_example_customer_completed_spend",
        "question": "Show the total completed-order spend for each customer.",
        "sql": """
SELECT
    c.customer_name,
    SUM(oi.quantity * p.price) AS completed_spend
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY c.customer_id, c.customer_name
ORDER BY completed_spend DESC, c.customer_name;
""",
        "description": "Calculate total completed-order spend for each customer using customer names and grouping by customer."
    },
    {
        "id": "sql_example_customers_with_cancelled_orders",
        "question": "Which customers have at least one cancelled order?",
        "sql": """
SELECT DISTINCT
    c.customer_name
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE o.status = 'Cancelled'
ORDER BY c.customer_name;
""",
        "description": "Find customer names associated with cancelled orders by joining customers to orders and returning distinct customers."
    },
    {
        "id": "sql_example_revenue_by_category",
        "question": "Which product category has the highest total revenue?",
        "sql": """
SELECT
    p.category,
    SUM(oi.quantity * p.price) AS revenue
FROM order_items AS oi
JOIN products AS p
    ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC, p.category
LIMIT 1;
""",
        "description": "Find the product category with the highest total revenue. Use revenue as the canonical output alias for SUM(quantity * product price), order by revenue descending with category as a deterministic tie-breaker, and return one category."
    },
    {
        "id": "sql_example_distinct_products_per_order",
        "question": "Show distinct products included in each order.",
        "sql": """
SELECT
    oi.order_id,
    COUNT(DISTINCT oi.product_id) AS distinct_products
FROM order_items AS oi
GROUP BY oi.order_id
ORDER BY oi.order_id;
""",
        "description": "For this grouped analytics request, return one row per order with the count of unique product identifiers. Interpret this wording as a distinct-product count per order, not a listing of individual product IDs or names."
    }

]
