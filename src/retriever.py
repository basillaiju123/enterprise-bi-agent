from src.schema_catalog import SCHEMA_CATALOG


def retrieve_schema(question: str) -> str:
    question_lower = question.lower()

    relevant_tables = []

    for item in SCHEMA_CATALOG:
        table = item["table"]
        description = item["description"]

        score = 0

        # Match table name
        if table.lower() in question_lower:
            score += 2

        # Match description words
        for word in description.lower().split():
            if len(word) > 4 and word in question_lower:
                score += 1

        # Match column names
        for column in item["columns"]:
            if column.lower() in question_lower:
                score += 2

        if score > 0:
            relevant_tables.append((score, item))

    # If nothing matched, return the full catalog
    if not relevant_tables:
        relevant_tables = [(0, item) for item in SCHEMA_CATALOG]

    # Highest relevance first
    relevant_tables.sort(key=lambda x: x[0], reverse=True)

    context = []

    for _, item in relevant_tables:
        context.append(f"Table: {item['table']}")
        context.append(f"Description: {item['description']}")

        for column, description in item["columns"].items():
            context.append(f"- {column}: {description}")

        context.append("")

    return "\n".join(context)