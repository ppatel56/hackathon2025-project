import langchain_community.utilities
from langchain_community.utilities import SQLDatabase
from typing import Any
from langchain_aws import ChatBedrock
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langgraph.prebuilt import ToolNode
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

db = SQLDatabase.from_uri("sqlite:///aws_logs.db")
print(db.dialect)
print(db.get_usable_table_names())
query = "SELECT COUNT(*) AS num_lambda_logs FROM lambda_logs;"
result = db.run(query)
print(result)

llm = ChatBedrock(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',  # or another available model
    model_kwargs=dict(temperature=0),
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN,
    region_name = 'us-east-1',
    beta_use_converse_api=False)


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

toolkit = SQLDatabaseToolkit(db=db, llm = llm)
tools = toolkit.get_tools()

list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")

print(list_tables_tool.invoke(""))

print(get_schema_tool.invoke("lambda_logs"))


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


query_check.invoke({"messages": [("user", "SELECT * FROM lambda_logs LIMIT 10;")]})

# Define Workflow

from typing import Annotated, Literal

from langchain_core.messages import AIMessage

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages


# Define the state for the agent
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# Define a new graph
workflow = StateGraph(State)


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
    ai_message = state["messages"][-1].tool_calls[0]['args']['final_answer']
    return {"messages": [query_check.invoke({"messages": [HumanMessage(content=ai_message)]})]}


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




# Describe a tool to represent the end state
class SubmitFinalAnswer(BaseModel):
    """Submit the final answer to the user based on the query results."""

    final_answer: str = Field(..., description="The final answer to the user")


# Add a node for a model to generate a query based on the question and schema
query_gen_system = """You are a SQL expert with a strong attention to detail.

Given a chain of messages, you will generate an appropriate sqlite query that answers that can help answer the user question.

Submit your query using SubmitFinalAnswer tool
"""


query_gen_prompt = ChatPromptTemplate.from_messages(
    [("system", query_gen_system), ("placeholder", "{messages}")]
)
query_gen = query_gen_prompt | llm.bind_tools(
    [SubmitFinalAnswer]
)



def query_gen_node(state: State):
    message = query_gen.invoke(state)
    
    return {"messages": [message]}


workflow.add_node("query_gen", query_gen_node)

# Add a node for a model to generate a query based on the question and schema
final_gen_system = """You are a SQL expert with a strong attention to detail.

Given a chain of messages, formulate a response that can help answer the user question

"""
final_gen_prompt = ChatPromptTemplate.from_messages(
    [("system", final_gen_system), ("placeholder", "{messages}")]
)
final_gen = final_gen_prompt | llm.bind_tools(
    [SubmitFinalAnswer]
)

def gen_final_answer(state: State):
    message = final_gen.invoke(state)
    
    return {"messages": [message]}

workflow.add_node("final_gen", gen_final_answer)

# Add a node for the model to check the query before executing it
workflow.add_node("correct_query", model_check_query)

# Add node for executing the query
workflow.add_node("execute_query", create_tool_node_with_fallback([db_query_tool]))


# Define a conditional edge to decide whether to continue or end the workflow
def should_continue(state: State) -> Literal[END, "correct_query", "query_gen"]:
    messages = state["messages"]
    last_message = messages[-1]
    # If there is a tool call, then we finish
    if getattr(last_message, "tool_calls", None):
        return END
    if last_message.content.startswith("Error:"):
        return "query_gen"
    else:
        return "correct_query"


# Specify the edges between the nodes
workflow.add_edge(START, "first_tool_call")
workflow.add_edge("first_tool_call", "list_tables_tool")
workflow.add_edge("list_tables_tool", "model_get_schema")
workflow.add_edge("model_get_schema", "get_schema_tool")
workflow.add_edge("get_schema_tool", "query_gen")
workflow.add_edge( "query_gen", "correct_query")
workflow.add_edge("correct_query", "execute_query")
workflow.add_edge("execute_query", "final_gen")
workflow.add_edge("final_gen", END)
# Compile the workflow into a runnable
app = workflow.compile()


#Visualize the graph

from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod

display(
    Image(
        app.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
        )
    )
)

# #run the agent
# query = "failed due to insufficient IAM permissions. what is this error related to? "
# try:
#     messages = app.invoke(
#         {"messages": [("user", query)]}
#     )
#     json_str = messages["messages"][-1].tool_calls[0]["args"]["final_answer"]
#     print(json_str)
# except Exception as e:
#     print(f"An error occured: {e}")

# messages = app.invoke(
#     {"messages": [("user", "how many cloudwatch logs do we have?")]}
# )
# json_str = messages["messages"][-1].tool_calls[0]["args"]["final_answer"]
# json_str

for event in app.stream(
    {"messages": [("user", "how many cloudwatch logs do we have related to lambda?")]}
):
    print(event)