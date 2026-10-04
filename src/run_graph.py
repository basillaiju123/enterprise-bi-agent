from src.graph import graph
from src.telemetry import trace_agent_run
FORCE_BAD_SQL = True

initial_state = {
    "user_question": "How many orders were completed by customers from India?",
    "schema_context": "",
    "generated_sql": "",
    "validation_error": "",
    "execution_error": "",
    "query_result": [],
    "retry_count": 0,
    "expected_result": [],
"evaluation_mode": False,
}
initial_state["generated_sql"] = """
SELECT COUNT(*) FROM orders WHERE status = 'Completed';
"""

# TEST: start with an intentionally incorrect SQL query
initial_state["generated_sql"] = """
SELECT COUNT(*) FROM orders WHERE status = 'Completed';
"""
trace_agent_run(initial_state["user_question"])
result = graph.invoke(initial_state)


print("\nGenerated SQL:")
print(result["generated_sql"])

print("\nValidation Error:")
print(result["validation_error"])

print("\nExecution Error:")
print(result["execution_error"])

print("\nQuery Result:")
for row in result["query_result"]:
    print(row)