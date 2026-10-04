from src.evaluation_node import evaluate_sql_node
from src.router import route_after_execution
from src.correction_node import correction_node
from src.nodes import generate_sql_node


state = {
    "user_question": "How many orders were completed by customers from India?",
    "schema_context": """
DATABASE SCHEMA CONTEXT

Table: customers
- customer_id
- country

Table: orders
- order_id
- customer_id
- status

BUSINESS KNOWLEDGE CONTEXT

Completed Order:
An order is considered completed when orders.status is equal to 'Completed'.
""",
    "generated_sql": """
SELECT COUNT(*) FROM orders WHERE status = 'Completed';
""",
    "validation_error": "",
    "execution_error": "",
    "query_result": [(5,)],
    "retry_count": 0,
}


print("=== First Evaluation ===")

state = evaluate_sql_node(state)

print("\nEvaluator:")
print(state["validation_error"])

decision = route_after_execution(state)

print("\nRouter:")
print(decision)


if decision == "retry":

    state = correction_node(state)

    print("\nRetry Count:")
    print(state["retry_count"])

    print("\n=== Generating Corrected SQL ===")

    state = generate_sql_node(state)

    print("\nCorrected SQL:")
    print(state["generated_sql"])