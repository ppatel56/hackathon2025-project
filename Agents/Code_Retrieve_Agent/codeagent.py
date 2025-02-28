from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
import os
from langchain_community.tools.file_management.read import ReadFileTool
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

system = """
You are a code retriever expert. 
You will call the appropriate tool to retrieve the code for the appropriate gluejob 
based on the user's request. The name of the file containing the code will always end with '.py'.
"""


prompt = ChatPromptTemplate.from_messages(
    [("system", system), ("placeholder", "{messages}")]
)

read_file_tool = ReadFileTool(
    description="Reads a file from the following path: 'glue_scripts/{jobname}'",
)

def create_code_agent():
    return create_react_agent(
        llm, tools=[read_file_tool], prompt=prompt
    )

if __name__ == "__main__":
    code_agent = create_code_agent()
    result = code_agent.invoke(
        {"messages": [{"role": "user", "content": "StockDataTransformation"}]}
    )
    print(result["messages"][-1].content)

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
