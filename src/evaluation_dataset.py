from datetime import date


EVALUATION_DATASET = [
    # ============================================================
    # 1–5: BASIC FILTERING
    # ============================================================

    {
        "question": "How many customers are from India?",
        "expected_result": [(2,)],
    },
    {
        "question": "Show the customer ID and customer name for customers from India.",
        "expected_result": [
            (2, "Bob"),
            (5, "Eva"),
        ],
    },
    {
        "question": "Which products are in the Accessories category?",
        "expected_result": [
            (102, "Mouse"),
            (103, "Keyboard"),
        ],
    },
    {
        "question": "Show the product ID and product name for products costing more than 100.",
        "expected_result": [
            (101, "Laptop"),
            (104, "Monitor"),
        ],
    },
    {
        "question": "Which orders were cancelled?",
        "expected_result": [
            (1003, 3, date(2025, 6, 5), "Cancelled"),
        ],
    },

    # ============================================================
    # 6–10: AGGREGATIONS
    # ============================================================

    {
        "question": "How many customers are there?",
        "expected_result": [(5,)],
    },
    {
        "question": "How many products are there?",
        "expected_result": [(5,)],
    },
    {
        "question": "How many orders are there?",
        "expected_result": [(6,)],
    },
    {
        "question": "What is the total order quantity?",
        "expected_result": [(12,)],
    },
    {
        "question": "What is the total revenue?",
        "expected_result": [(3065.0,)],
    },

    # ============================================================
    # 11–14: SORTING / TOP-N
    # ============================================================

    {
        "question": "What is the most expensive product?",
        "expected_result": [
            ("Laptop", 900.0),
        ],
    },
    {
        "question": "What is the cheapest product?",
        "expected_result": [
            ("Mouse", 25.0),
        ],
    },
    {
        "question": "What are the three most expensive products?",
        "expected_result": [
            ("Laptop", 900.0),
            ("Monitor", 300.0),
            ("Headphones", 80.0),
        ],
    },
    {
        "question": "What are the two cheapest products?",
        "expected_result": [
            ("Mouse", 25.0),
            ("Keyboard", 50.0),
        ],
    },

    # ============================================================
    # 15–19: JOINS
    # ============================================================

    {
        "question": "How many orders were completed by customers from India?",
        "expected_result": [(3,)],
    },
    {
        "question": "What are the names of customers who placed orders?",
        "expected_result": [
            ("Alice",),
            ("Bob",),
            ("Charlie",),
            ("David",),
            ("Eva",),
        ],
    },
    {
        "question": "Show the product ID and product name for products that were ordered.",
        "expected_result": [
            (101, "Laptop"),
            (102, "Mouse"),
            (103, "Keyboard"),
            (104, "Monitor"),
            (105, "Headphones"),
        ],
    },
    {
        "question": "Show the product ID and total units ordered for each product.",
        "expected_result": [
            (101, 2),
            (102, 3),
            (103, 1),
            (104, 3),
            (105, 3),
        ],
    },
    {
        "question": "Show the customer ID and number of completed orders for each customer who placed a completed order.",
        "expected_result": [
            (1, 1),
            (2, 2),
            (4, 1),
            (5, 1),
        ],
    },

    # ============================================================
    # 20–24: BUSINESS DEFINITIONS
    # ============================================================

    {
        "question": "What is the completed order count?",
        "expected_result": [(5,)],
    },
    {
        "question": "What is the cancelled order count?",
        "expected_result": [(1,)],
    },
    {
        "question": "What is the completed revenue?",
        "expected_result": [(2985.0,)],
    },
    {
        "question": "What is the cancelled revenue?",
        "expected_result": [(80.0,)],
    },
    {
        "question": "What is the average order value for completed orders?",
        "expected_result": [(597.0,)],
    },

    # ============================================================
    # 25–27: MULTI-CONDITION QUERIES
    # ============================================================

    {
        "question": "Show the product ID, product name, and price for Electronics products costing more than 500.",
        "expected_result": [
            (101, "Laptop", 900.0),
        ],
    },
    {
        "question": "Show the order ID and order date for completed orders placed in June 2025.",
        "expected_result": [
            (1001, date(2025, 6, 1)),
            (1002, date(2025, 6, 3)),
            (1004, date(2025, 6, 10)),
            (1005, date(2025, 6, 12)),
            (1006, date(2025, 6, 15)),
        ],
    },
    {
        "question": "What are the names of customers from India who placed completed orders?",
        "expected_result": [
            ("Bob",),
            ("Eva",),
        ],
    },

    # ============================================================
    # 28–30: EDGE / NEGATIVE CASES
    # ============================================================

    {
        "question": "Which products are in the Furniture category?",
        "expected_result": [],
    },
    {
        "question": "Which customers are from Canada?",
        "expected_result": [],
    },
    {
        "question": "Which orders have Pending status?",
        "expected_result": [],
    },
]