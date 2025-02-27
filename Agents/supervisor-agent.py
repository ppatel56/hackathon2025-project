from typing import Literal
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from CRAG_agent import crag_workflow
from SQL_agent import sql_agent
from Code_Retrieve_Agent import codeagent
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated, Literal

#from langgraph.prebuilt import create_react_agent # Change for crag agent func
from agents import create_crag_agent

from dotenv import load_dotenv

import sys
import os

# These are the different AI Agents that the supervisor can pick from
members = ['SQL Query Agent', 'CRAG Agent', 'Code Retriever Agent']

# Decides when the work is completed
options = members + ['FINISH']

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]

llm = ChatOpenAI(model="gpt-4o", temperature=0)

class State(MessagesState):
    next: str
    messages: Annotated[list[AnyMessage], add_messages]

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    print("-----------------")
    print("supervisor_node")
    print(state)
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto, "messages": state["messages"][-1]})

def construct_super_graph():
    #define agents (subgraphs)
    crag_ag = crag_workflow.create_crag_agent()
    sql_ag = sql_agent.create_sql_agent()
    code_age = codeagent.create_code_agent()

    def crag_node(state: State) -> Command[Literal[ "supervisor"]]:
        result = crag_ag.invoke({"question":state["messages"][-1].content})
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="crag")
                ]
            },
            goto="supervisor",
        )





