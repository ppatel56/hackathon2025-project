from supervisor_agent import (
    State,
    HumanMessage,
    graph  # Import the compiled graph
)

# Simulate user inputs
test_inputs = [
    "Generate a SQL query to find all users who signed up in the last month.",
    "Retrieve the latest code changes from the repository.",
    "Summarize the results and finish the task."
]

def test_langgraph():
    # Initialize the state
    state = State(messages=[])

    for input in test_inputs:
        # Add user input to the state
        state.messages.append(HumanMessage(content=input))

        # Run the graph with the current state
        state = graph.invoke(state)

        # Print the result of the last agent's action
        print(f"Agent Response: {state.messages[-1].content}")

        # Check if the task is completed
        if state.messages[-1].content == "Task completed.":
            print("Supervisor: Task completed. Exiting.")
            break

# Run the test
if __name__ == "__main__":
    test_langgraph()