from langfuse import observe


@observe()
def trace_agent_run(question: str):
    return {
        "question": question,
    }