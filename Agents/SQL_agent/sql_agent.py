import langchain_community.utilities
from langchain_community.utilities import SQLDatabase
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from typing import Annotated, Literal
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages
import os

# Define the SQLite database file
db_file = os.path.join(os.path.dirname(__file__), 'aws_logs.db')

# Ensure the database file exists
if not os.path.exists(db_file):
    raise FileNotFoundError(f"Database file '{db_file}' not found. Please run 'create_sqlite_db.py' to create the database.")


db = SQLDatabase.from_uri(f"sqlite:///{db_file}")
print(db.dialect)
print(db.get_usable_table_names())
# query = "SELECT COUNT(*) AS num_lambda_logs FROM lambda_logs;"
# result = db.run(query)
# print(result)

llm = ChatOpenAI(model="gpt-4o", temperature=0)
sql_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def create_tool_node_with_fallback(tools: list) -> RunnableWithFallbacks[Any, dict]:
    """
    Create a ToolNode with a fallback to handle errors and surface them to the agent.
    """
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

toolkit = SQLDatabaseToolkit(db=db, llm = sql_llm)
tools = toolkit.get_tools()

list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")

#Manual db_query_tool

@tool
def db_query_tool(query: str) -> str:
    """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    result = db.run_no_throw(query)
    if not result:
        return "Error: Query failed. Please rewrite your query and try again."
    return result


print(db_query_tool.invoke("SELECT * FROM lambda_logs LIMIT 10;"))

#chatprompt template

query_check_system = """You are a SQL expert with a strong attention to detail.
Double check the SQLite query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

You will call the appropriate tool to execute the query after running this check."""

query_check_prompt = ChatPromptTemplate.from_messages(
    [("system", query_check_system), ("placeholder", "{messages}")]
)
query_check = query_check_prompt | llm.bind_tools(
    [db_query_tool]
)


# query_check.invoke({"messages": [("user", "SELECT * FROM lambda_logs LIMIT 10;")]})

# Define the state for the agent
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Add a node for the first tool call
def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "sql_db_list_tables",
                        "args": {},
                        "id": "tool_abcd123",
                    }
                ],
            )
        ]
    }


def model_check_query(state: State) -> dict[str, list[AIMessage]]:
    """
    Use this tool to double-check if your query is correct before executing it.
    """
    return {"messages": [query_check.invoke({"messages": [state["messages"][-1]]})]}


query_gen_system = """You are a SQL expert with a strong attention to detail.

    You can define SQL queries, analyze queries results and interpretate query results to response an answer.

    Read the messages bellow and identify the user question, table schemas, query statement and query result, or error if they exist.

    1. If there's not any query result that make sense to answer the question, create a syntactically correct SQLite query to answer the user question. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    2. If you create a query, response ONLY the query statement. For example, "SELECT id, name FROM pets;"

    3. If a query was already executed, but there was an error. Response with the same error message you found. For example: "Error: Pets table doesn't exist"

    4. If a query was already executed successfully interpretate the response and answer the question following this pattern: Answer: <<question answer>>. For example: "Answer: There three cats registered as adopted"
"""


query_gen_prompt = ChatPromptTemplate.from_messages(
    [("system", query_gen_system), ("placeholder", "{messages}")]
)
query_gen = query_gen_prompt | llm


def query_gen_node(state: State):
    message = query_gen.invoke(state)
    
    return {"messages": [message]}


# Conditional Function
def should_continue(state: State) -> Literal[END, "correct_query", "query_gen"]:
    messages = state["messages"]
    
    last_message = messages[-1]
    if last_message.content.startswith("Answer:"):
        return END
    if last_message.content.startswith("Error:"):
        return "query_gen"
    else:
      return "correct_query"
    
def create_sql_agent():

    # Define a new graph
    workflow = StateGraph(State)

    workflow.add_node("first_tool_call", first_tool_call)
    # Add nodes for the first two tools
    workflow.add_node(
        "list_tables_tool", create_tool_node_with_fallback([list_tables_tool])
    )
    workflow.add_node("get_schema_tool", create_tool_node_with_fallback([get_schema_tool]))
    # Add a node for a model to choose the relevant tables based on the question and available tables
    model_get_schema = llm.bind_tools(
        [get_schema_tool]
    )
    workflow.add_node(
        "model_get_schema",
        lambda state: {
            "messages": [model_get_schema.invoke(state["messages"])],
        },
    )
    #create node
    workflow.add_node("query_gen", query_gen_node)
    # Add a node for the model to check the query before executing it
    workflow.add_node("correct_query", model_check_query)
    # Add node for executing the query
    workflow.add_node("execute_query", create_tool_node_with_fallback([db_query_tool]))

    # Specify the edges between the nodes
    workflow.add_edge(START, "first_tool_call")
    workflow.add_edge("first_tool_call", "list_tables_tool")
    workflow.add_edge("list_tables_tool", "model_get_schema")
    workflow.add_edge("model_get_schema", "get_schema_tool")
    workflow.add_edge("get_schema_tool", "query_gen")
    workflow.add_conditional_edges(
        "query_gen",
        should_continue,
    )
    workflow.add_edge("correct_query", "execute_query")
    workflow.add_edge("execute_query", "query_gen")

    # Compile the workflow into a runnable
    app = workflow.compile()

    return app

if __name__ == "__main__":
    # messages = app.invoke(
    #     {"messages": [("user", "how many cloudwatch logs do we have?")]}
    # )
    app = create_sql_agent()
    for event in app.stream(
        {"messages": [("user", "how many cloudwatch logs do we have related to lambda?")]}
    ):
        print(event)
    print()