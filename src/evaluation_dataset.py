EVALUATION_DATASET = [
    {
        "question": "How many customers are from India?",
        "expected_result": [(2,)],
        "expected_sql_requirements": [
            "Use the customers table.",
            "Filter customers where country is India.",
            "Return the count of matching customers.",
        ],
    },
    {
        "question": "What products are in the Electronics category?",
        "expected_result": [
            (101, "Laptop"),
            (104, "Monitor"),
        ],
        "expected_sql_requirements": [
            "Use the products table.",
            "Filter category to Electronics.",
            "Return products belonging to the Electronics category.",
        ],
    },
    {
        "question": "What is the most expensive product?",
        "expected_result": [
            ("Laptop", 900.0),
        ],
        "expected_sql_requirements": [
            "Use the products table.",
            "Identify the product with the highest price.",
            "Return the most expensive product.",
        ],
    },
    {
        "question": "How many orders were completed?",
        "expected_result": [(5,)],
        "expected_sql_requirements": [
            "Use the orders table.",
            "Filter status to Completed.",
            "Count the completed orders.",
        ],
    },
    {
        "question": "How many orders were completed by customers from India?",
        "expected_result": [(3,)],
        "expected_sql_requirements": [
            "Use orders and customers.",
            "Join orders to customers using customer_id.",
            "Filter orders where status is Completed.",
            "Filter customers where country is India.",
            "Count the matching orders.",
        ],
    },
    {
        "question": "What is the revenue?",
        "expected_result": [(3065.0,)],
        "expected_sql_requirements": [
            "Use order_items and products.",
            "Join order_items to products using product_id.",
            "Calculate revenue as quantity multiplied by product price.",
            "Sum quantity multiplied by price.",
            "Do not filter by order status unless the question explicitly asks for completed revenue.",
        ],
    },
]