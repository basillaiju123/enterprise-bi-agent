from src.business_catalog import BUSINESS_CATALOG


def retrieve_business_knowledge(question: str) -> str:
    question_lower = question.lower()

    relevant = []

    for item in BUSINESS_CATALOG:
        score = 0

        term_words = item["term"].lower().split()

        for word in term_words:
            if word in question_lower:
                score += 2

        definition_words = item["definition"].lower().split()

        for word in definition_words:
            if len(word) > 5 and word in question_lower:
                score += 1

        if score > 0:
            relevant.append((score, item))

    relevant.sort(key=lambda x: x[0], reverse=True)

    # No match → return all business definitions
    if not relevant:
        relevant = [(0, item) for item in BUSINESS_CATALOG]

    context = []

    for _, item in relevant:
        context.append(f"Business Term: {item['term']}")
        context.append(f"Definition: {item['definition']}")
        context.append(f"SQL Logic: {item['sql_logic']}")
        context.append("")

    return "\n".join(context)