import duckdb

DB_PATH = "data/sample_warehouse.duckdb"


def execute_query(sql: str):
    con = duckdb.connect(DB_PATH)

    try:
        result = con.execute(sql).fetchall()
        columns = [column[0] for column in con.description]

        return columns, result
    finally:
        con.close()


if __name__ == "__main__":
    sql = """
    SELECT
        country,
        COUNT(*) AS customer_count
    FROM customers
    GROUP BY country
    ORDER BY customer_count DESC;
    """

    columns, rows = execute_query(sql)

    print("Columns:", columns)

    for row in rows:
        print(row)