from typing import Literal
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage

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

llm = ChatAnthropic(
    model='amazon.nova-pro-v1:0',  # or another available model
    model_kwargs=dict(temperature=0),
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN,
    region_name = 'us-east-1'
)

class State(MessagesState):
    next: str

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})





