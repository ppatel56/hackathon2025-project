from typing import Literal
from typing import TypedDict
print('it works')
import sys
print(sys.path)
import sys
sys.path.append(r'C:\ProgramData\UserDataFolders\S-1-5-21-1112896083-289523540-421599246-1009\Documents\hackathon2025-project\env\Lib\site-packages')
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage

#from langgraph.prebuilt import create_react_agent # Change for crag agent func
# from agents import create_crag_agent

from dotenv import load_dotenv

import sys
import os

# Load environment variables from .env file
load_dotenv()

# Reference the environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
CLAUDE_AI_KEY = os.getenv('CLAUDE_AI_KEY')

def create_sql_query_agent():
    """Simulate the SQL Query Agent."""
    def run(query: str) -> str:
        return f"SQL Query Agent: Generated SQL query for '{query}'."
    return run

def create_crag_agent():
    """Simulate the CRAG Agent."""
    def run(query: str) -> str:
        return f"CRAG Agent: Retrieved code changes for '{query}'."
    return run

def create_code_retrieval_agent():
    """Simulate the Code Retrieval Agent."""
    def run(query: str) -> str:
        return f"Code Retrieval Agent: Retrieved code for '{query}'."
    return run

# aws_access_key_id=AWS_ACCESS_KEY_ID
# aws_secret_access_key=AWS_SECRET_ACCESS_KEY
# aws_session_token=AWS_SESSION_TOKEN

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
    model='claude-3-sonnet-20240229',  # or another available model
    temperature=0,  # Pass temperature explicitly
    api_key=CLAUDE_AI_KEY
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





