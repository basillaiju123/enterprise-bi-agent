from src.schema_catalog import SCHEMA_CATALOG
from src.business_catalog import BUSINESS_CATALOG


BUSINESS_SYNONYMS = {
    "Revenue": [
        "sales",
        "total sales",
        "income",
        "earnings",
        "money generated",
        "money made",
        "sales revenue",
        "total revenue",
    ],
    "Completed Order": [
        "successful order",
        "finished order",
        "successful purchase",
        "completed purchase",
        "orders completed",
    ],
    "Cancelled Order": [
        "failed order",
        "cancelled purchase",
        "canceled order",
        "orders cancelled",
        "orders canceled",
    ],
    "Order Quantity": [
        "units sold",
        "items sold",
        "number of items",
        "quantity sold",
        "total units",
    ],
    "Average Order Value": [
        "average purchase value",
        "average sale",
        "average revenue per order",
        "average order revenue",
    ],
}


def build_knowledge_documents() -> list[dict]:
    documents = []

    # Schema documents
    for item in SCHEMA_CATALOG:
        table = item["table"]
        description = item["description"]

        columns = "\n".join(
            f"- {column}: {column_description}"
            for column, column_description in item["columns"].items()
        )

        text = f"""Database schema information.

Table: {table}

Description:
{description}

Columns:
{columns}

This table may be relevant to questions about:
{description}
"""

        documents.append(
            {
                "id": f"schema_{table}",
                "type": "schema",
                "source": table,
                "text": text,
            }
        )

    # Business definition documents
    for item in BUSINESS_CATALOG:
        term = item["term"]

        synonyms = BUSINESS_SYNONYMS.get(term, [])

        synonym_text = ", ".join(synonyms)

        text = f"""Business metric definition.

Business Term:
{term}

Definition:
{item["definition"]}

SQL Logic:
{item["sql_logic"]}

Related business concepts:
{synonym_text}
"""

        documents.append(
            {
                "id": f"business_{term.lower().replace(' ', '_')}",
                "type": "business",
                "source": term,
                "text": text,
            }
        )

    return documents
