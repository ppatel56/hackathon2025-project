from supervisor_agent import (
    supervisor_node,
    State,
    HumanMessage,
    END
)

# Simulate user input
test_inputs = [
    "Generate a SQL query to find all users who signed up in the last month.",
    "Retrieve the latest code changes from the repository.",
    "Summarize the results and finish the task."
]

def simulate_agent_response(agent_name: str, input: str) -> str:
    """Simulate an agent's response based on the input."""
    if agent_name == 'SQL Query Agent':
        return f"SQL Query Agent: Generated SQL query for '{input}'."
    elif agent_name == 'CRAG Agent':
        return f"CRAG Agent: Retrieved code changes for '{input}'."
    elif agent_name == 'Code Retriever Agent':
        return f"Code Retriever Agent: Retrieved code for '{input}'."
    else:
        return f"Unknown agent: {agent_name}"

def test_supervisor():
    # Initialize the state
    state = State(messages=[], next=None)

    for input in test_inputs:
        # Add user input to the state
        state["messages"].append(HumanMessage(content=input))

        # Call the supervisor node to decide the next action
        command = supervisor_node(state)

        if command.goto == END:
            print("Supervisor: Task completed. Exiting.")
            break

        # Simulate the agent's response
        agent_response = simulate_agent_response(command.goto, input)
        print(agent_response)

        # Add the agent's response to the state
        state["messages"].append(HumanMessage(content=agent_response))

# Run the test
if __name__ == "__main__":
    test_supervisor()