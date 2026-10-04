import duckdb
from pathlib import Path

DB_PATH = Path("data/sample_warehouse.duckdb")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH))

# -------------------------
# Customers
# -------------------------
con.execute("""
CREATE TABLE customers (
    customer_id INTEGER,
    customer_name VARCHAR,
    country VARCHAR,
    signup_date DATE
)
""")

# -------------------------
# Products
# -------------------------
con.execute("""
CREATE TABLE products (
    product_id INTEGER,
    product_name VARCHAR,
    category VARCHAR,
    price DOUBLE
)
""")

# -------------------------
# Orders
# -------------------------
con.execute("""
CREATE TABLE orders (
    order_id INTEGER,
    customer_id INTEGER,
    order_date DATE,
    status VARCHAR
)
""")

# -------------------------
# Order Items
# -------------------------
con.execute("""
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
)
""")

# -------------------------
# Insert customers
# -------------------------
con.execute("""
INSERT INTO customers VALUES
(1, 'Alice', 'USA', '2025-01-10'),
(2, 'Bob', 'India', '2025-02-15'),
(3, 'Charlie', 'UK', '2025-03-20'),
(4, 'David', 'Germany', '2025-04-05'),
(5, 'Eva', 'India', '2025-05-12')
""")

# -------------------------
# Insert products
# -------------------------
con.execute("""
INSERT INTO products VALUES
(101, 'Laptop', 'Electronics', 900.00),
(102, 'Mouse', 'Accessories', 25.00),
(103, 'Keyboard', 'Accessories', 50.00),
(104, 'Monitor', 'Electronics', 300.00),
(105, 'Headphones', 'Audio', 80.00)
""")

# -------------------------
# Insert orders
# -------------------------
con.execute("""
INSERT INTO orders VALUES
(1001, 1, '2025-06-01', 'Completed'),
(1002, 2, '2025-06-03', 'Completed'),
(1003, 3, '2025-06-05', 'Cancelled'),
(1004, 2, '2025-06-10', 'Completed'),
(1005, 4, '2025-06-12', 'Completed'),
(1006, 5, '2025-06-15', 'Completed')
""")

# -------------------------
# Insert order items
# -------------------------
con.execute("""
INSERT INTO order_items VALUES
(1001, 101, 1),
(1001, 102, 2),
(1002, 104, 1),
(1002, 103, 1),
(1003, 105, 1),
(1004, 101, 1),
(1005, 104, 2),
(1006, 105, 2),
(1006, 102, 1)
""")

print("Database created successfully.")

con.close()