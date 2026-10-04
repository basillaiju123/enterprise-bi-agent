from src.guardrails.validator import validate_sql


tests = [
    "SELECT * FROM customers",
    "SELECT COUNT(*) FROM orders",
    "DELETE FROM customers",
    "DROP TABLE customers",
    "SELECT * FROM customers; SELECT * FROM products",
]


for sql in tests:
    valid, message = validate_sql(sql)

    print("\nSQL:")
    print(sql)

    print("Valid:", valid)
    print("Message:", message)
