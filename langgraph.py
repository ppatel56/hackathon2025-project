import sys
sys.path.append(r'C:\ProgramData\UserDataFolders\S-1-5-21-1112896083-289523540-421599246-1009\Documents\hackathon2025-project\env\Lib\site-packages')

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from typing import Literal
from langgraph.types import Command
## Added additonal imports for create_crag_agent, sql_query_agent, and code_retriever_agent ##

# Define the state
class State:
    messages: list

# Create your custom agents
sql_query_agent = create_sql_query_agent()
crag_agent = create_crag_agent()
code_retrieval_agent = create_code_retrieval_agent()
supervisor_node = supervisor_node()

def supervisor_node(state: State) -> Command[Literal["sql_query_agent", "crag_agent", "code_retrieval_agent", "END"]]:
    """Supervisor decides which agent to invoke next."""
    last_message = state.messages[-1].content

    if "SQL" in last_message:
        return Command(goto="sql_query_agent")
    elif "CRAG" in last_message:
        return Command(goto="crag_agent")
    elif "code" in last_message:
        return Command(goto="code_retrieval_agent")
    else:
        return Command(goto="END")

# Define the SQL Query Agent node
def sql_query_agent_node(state: State) -> Command[Literal["supervisor"]]:
    result = sql_query_agent.run(state.messages[-1].content)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result, name="sql_query_agent")
            ]
        },
        goto="supervisor",
    )

# Define the CRAG Agent node
def crag_agent_node(state: State) -> Command[Literal["supervisor"]]:
    result = crag_agent.run(state.messages[-1].content)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result, name="crag_agent")
            ]
        },
        goto="supervisor",
    )

# Define the Code Retrieval Agent node
def code_retrieval_agent_node(state: State) -> Command[Literal["supervisor"]]:
    result = code_retrieval_agent.run(state.messages[-1].content)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result, name="code_retrieval_agent")
            ]
        },
        goto="supervisor",
    )

# Build the graph
builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("sql_query_agent", sql_query_agent_node)
builder.add_node("crag_agent", crag_agent_node)
builder.add_node("code_retrieval_agent", code_retrieval_agent_node)

# Add edges for the supervisor
builder.add_edge("sql_query_agent", "supervisor")
builder.add_edge("crag_agent", "supervisor")
builder.add_edge("code_retrieval_agent", "supervisor")

# Compile the graph
graph = builder.compile()