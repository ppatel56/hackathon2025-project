from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from aws_creds import *
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
import os

llm = ChatBedrock(
    model='amazon.nova-pro-v1:0',  # or another available model
    model_kwargs=dict(temperature=0),
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN,
    region_name = 'us-east-1'
)

@tool
def return_code_tool(
    # code: Annotated[str, "The code for the Glue job"], 
    jobname: str
):
    """Use this to retrieve code"""
    f = open(jobname, 'r')
    data = f.read()
    return data

code_agent = create_react_agent(
    llm, tools=[return_code_tool]
)
print(code_agent)

result = code_agent.invoke(
    {"messages": [{"role": "user", "content": "Hackathon-Test-Glue-1.py"}]}
)
print(result)

# def code_node(state: State) -> Command[Literal["supervisor"]]:
#     result = code_agent.invoke(state)
#     return Command(
#         update={
#             "messages": [
#                 HumanMessage(content=result["messages"][-1].content, name="coder")
#             ]
#         },
#         goto="supervisor",
#     )
