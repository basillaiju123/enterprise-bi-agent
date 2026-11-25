
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
        "id": "sql_example_completed_orders_india_alias",
        "question": "How many completed orders were placed by customers from India?",
        "sql": """
SELECT COUNT(DISTINCT o.order_id) AS completed_orders
FROM orders AS o
JOIN customers AS c
    ON o.customer_id = c.customer_id
WHERE o.status = 'Completed'
  AND c.country = 'India';
""",
        "description": "Count distinct completed orders placed by Indian customers and use completed_orders as the exact output alias."
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
        "id": "sql_example_units_sold_all_order_items",
        "question": "How many units were purchased across all order items, regardless of order status?",
        "sql": """
SELECT SUM(quantity) AS units_sold
FROM order_items;
""",
        "description": "Sum quantity across every order-item record without filtering by order status. Use units_sold as the exact output alias."
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
    },
    {
        "id": "sql_example_completed_units_alias",
        "question": "How many units were included in completed orders?",
        "sql": """
SELECT
    SUM(oi.quantity) AS completed_units
FROM orders AS o
JOIN order_items AS oi
    ON o.order_id = oi.order_id
WHERE o.status = 'Completed';
""",
        "description": "Sum item quantities only for orders whose status is Completed. Join orders to order_items by order_id and use completed_units as the exact output alias."
    },
    {
        "id": "sql_example_units_ordered_per_product",
        "question": "How many units of each product have been ordered?",
        "sql": """
SELECT
    p.product_name,
    COALESCE(SUM(oi.quantity), 0) AS units_ordered
FROM products AS p
LEFT JOIN order_items AS oi
    ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
ORDER BY p.product_name;
""",
        "description": "Return one row for every product, including products with no order items. Use a LEFT JOIN from products to order_items, COALESCE the summed quantity to zero, and use units_ordered as the output alias."
    },
    {
        "id": "sql_example_completed_orders_by_country",
        "question": "Show completed order counts for each customer country.",
        "sql": """
SELECT
    c.country,
    COUNT(DISTINCT o.order_id) AS completed_orders
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY c.country
ORDER BY c.country;
""",
        "description": "Count distinct completed orders for each customer country. Use completed_orders as the output alias and sort countries alphabetically."
    },
    {
        "id": "sql_example_latest_order_date_alias",
        "question": "What is the most recent order date?",
        "sql": """
SELECT MAX(order_date) AS latest_order_date
FROM orders;
""",
        "description": "Return the latest order date using MAX(order_date) and the exact output alias latest_order_date."
    },
    {
        "id": "sql_example_completed_orders_after_date_alias",
        "question": "Count completed orders placed on or after June 10, 2025.",
        "sql": """
SELECT COUNT(*) AS completed_orders
FROM orders
WHERE status = 'Completed'
  AND order_date >= DATE '2025-06-10';
""",
        "description": "Count orders with Completed status on or after June 10, 2025, using an inclusive date boundary and the exact output alias completed_orders."
    },
    {
        "id": "sql_example_average_quantity_per_item_record",
        "question": "What is the average quantity per order-item record?",
        "sql": """
SELECT AVG(quantity) AS average_quantity
FROM order_items;
""",
        "description": "Calculate the arithmetic average of quantity across order_items records and use average_quantity as the exact output alias."
    },
    {
        "id": "sql_example_completed_orders_and_revenue_by_country",
        "question": "For each country, show the number of completed orders and completed revenue.",
        "sql": """
SELECT
    c.country,
    COUNT(DISTINCT o.order_id) AS completed_orders,
    SUM(oi.quantity * p.price) AS completed_revenue
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
JOIN order_items AS oi
    ON o.order_id = oi.order_id
JOIN products AS p
    ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY c.country
ORDER BY c.country;
""",
        "description": "For each customer country, count distinct completed orders and sum completed-order line revenue. Use the exact aliases completed_orders and completed_revenue, grouping and ordering by country."
    },
    {
        "id": "sql_example_completed_orders_per_month_2025",
        "question": "Calculate the number of completed orders per month in 2025.",
        "sql": """
SELECT
    DATE_TRUNC('month', order_date) AS order_month,
    COUNT(*) AS completed_orders
FROM orders
WHERE status = 'Completed'
  AND order_date >= DATE '2025-01-01'
  AND order_date < DATE '2026-01-01'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY order_month;
""",
        "description": "Count completed orders by calendar month during 2025. Use the half-open 2025 date range, output aliases order_month and completed_orders, and order chronologically by order_month."
    },
    {
        "id": "sql_example_total_units_by_category",
        "question": "Show the total quantity sold for each product category.",
        "sql": """
SELECT
    p.category,
    SUM(oi.quantity) AS total_units
FROM order_items AS oi
JOIN products AS p
    ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY p.category;
""",
        "description": "Sum ordered item quantities by product category. Use total_units as the exact output alias and sort categories alphabetically."
    },
    {
        "id": "sql_example_completed_order_value_by_order",
        "question": "Calculate the total value of all completed orders for each order ID.",
        "sql": """
SELECT
    o.order_id,
    SUM(oi.quantity * p.price) AS order_value
FROM orders AS o
JOIN order_items AS oi
    ON o.order_id = oi.order_id
JOIN products AS p
    ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY o.order_id
ORDER BY o.order_id;
""",
        "description": "Calculate each completed order's value by summing quantity multiplied by product price. Filter to Completed orders, use order_value as the output alias, and order by order_id."
    }
,

    {
        "id": "sql_example_top_three_customers_completed_orders",
        "question": "Show the top three customers by number of completed orders.",
        "sql": """
SELECT
    c.customer_name,
    COUNT(*) AS completed_order_count
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY c.customer_id, c.customer_name
ORDER BY completed_order_count DESC, c.customer_name
LIMIT 3;
""",
        "description": "Return the three customers with the highest completed-order counts. Use completed_order_count as the metric alias and customer_name as a deterministic alphabetical tie-breaker after the count descending."
    },
    {
        "id": "sql_example_orders_for_customer_id",
        "question": "Show all orders placed by customer ID 2.",
        "sql": """
SELECT
    order_id,
    order_date,
    status
FROM orders
WHERE customer_id = 2
ORDER BY order_date, order_id;
""",
        "description": "List order IDs, dates, and statuses for customer ID 2. Treat customer_id only as a filter and do not include it in the output projection."
    },
    {
        "id": "sql_example_item_record_count_per_order",
        "question": "For each order, show its ID and number of item records.",
        "sql": """
SELECT
    order_id,
    COUNT(*) AS item_record_count
FROM order_items
GROUP BY order_id
ORDER BY order_id;
""",
        "description": "Count order-item records per order, not the sum of quantities. Use item_record_count as the exact metric alias and order by order_id."
    },
    {
        "id": "sql_example_successful_purchases_by_country",
        "question": "Count successful purchases by customer country.",
        "sql": """
SELECT
    c.country,
    COUNT(DISTINCT o.order_id) AS successful_purchases
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY c.country
ORDER BY c.country;
""",
        "description": "Count distinct orders with Completed status by customer country. In this benchmark, successful purchases means completed orders. Use successful_purchases as the exact alias and sort by country."
    },
    {
        "id": "sql_example_units_sold_by_product_name",
        "question": "Show total items sold by product name.",
        "sql": """
SELECT
    p.product_name,
    SUM(oi.quantity) AS units_sold
FROM products AS p
JOIN order_items AS oi
    ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
ORDER BY p.product_name;
""",
        "description": "Sum item quantities for each product that appears in order_items. Use units_sold as the exact alias and sort product names alphabetically."
    }
]
