from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
import os

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

@tool
def return_code_tool(
    # code: Annotated[str, "The code for the Glue job"], 
    jobname: str
):
    """Use this to retrieve code"""
    f = open(f'glue_scripts/{jobname}', 'r')
    data = f.read()
    return data

def create_code_agent():
    return create_react_agent(
        llm, tools=[return_code_tool]
    )

if __name__ == "__main__":
    code_agent = create_code_agent()
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
