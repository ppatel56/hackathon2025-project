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
from typing import List
from pydantic import BaseModel, Field

#from langgraph.prebuilt import create_react_agent # Change for crag agent func

from dotenv import load_dotenv

import sys
import os

# These are the different AI Agents that the supervisor can pick from
members = ['Query_Internal_Docs_and_web', 'Query_Cloudwatch', 'Retrieve_App_Code']
# members = ['Query_Cloudwatch'] #, 'Query_Cloudwatch', 'Retrieve_App_Code']

# Decides when the work is completed
options = members

sup_system_prompt = f"""
You are a task router assistant.
Route to the appropriate worker to complete the step in the user request. 
Available workers to route to: {members}.
    
"""

crag_q_system_prompt = (
    "You are a professional RAG question generator. Given the following user request, respond"
    " with a question to ask the CRAG agent. The question should be designed to elicit a response"
    " that will help the user. When finished, respond with FINISH."
)

synthesizer_prompt = """
You are a professional response synthesizer. Given the following messages, respond with a synthesized response. 
Ignore any messages that are not relevant to the original user question when synthesizing your response.
Respond only with the synthesized response.
"""


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]

class CRagQuestion(BaseModel):
    """Question to ask the CRAG agent."""
    question: str = Field(
        description="Question to ask the CRAG agent'"
    )

llm = ChatOpenAI(model="gpt-4o", temperature=0)

class State(MessagesState):
    next: str
    documents: List[str]
    links: List[str]
    final_response: str
    

def supervisor_node(state: State) -> Command[Literal[*members]]:
    print("-----------------")
    print("supervisor_node")
    messages = [
        {"role": "system", "content": sup_system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    print("Next: ", response["next"])
    goto = response["next"]

    return Command(goto=goto, update={"next": goto})

def construct_super_graph():
    #define agents (subgraphs)
    crag_ag = crag_workflow.create_crag_agent()
    sql_ag = sql_agent.create_sql_agent()
    code_age = codeagent.create_code_agent()

    def crag_node(state: State) -> Command[Literal[ "supervisor"]]:
        print("-----------------")
        print("crag_node")

        messages = [
            {   "role": "system", "content": crag_q_system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(CRagQuestion).invoke(messages)
        
        result = crag_ag.invoke({"question":response.question})

        # Ensure unique values in documents and links
        updated_documents = result["documents"]
        updated_links = result["links"]
        
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["generation"], name="crag")
                ],
                "documents": updated_documents,
                "links": updated_links
            },
            goto=END,
        )
    
    def sql_node(state: State) -> Command[Literal[ "supervisor"]]:
        print("-----------------")
        print("sql_node")
        result = sql_ag.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="sql")
                ]
            },
            goto=END,
        )
    
    def code_node(state: State) -> Command[Literal[ "supervisor"]]:
        print("-----------------")
        print("code_node")
        result = code_age.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="coder")
                ]
            },
            goto=END,
        )
    
    # Define a new graph
    workflow = StateGraph(State)
    workflow.add_edge(START, "supervisor")
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("Query_Internal_Docs_and_web", crag_node)
    workflow.add_node("Query_Cloudwatch", sql_node)
    workflow.add_node("Retrieve_App_Code", code_node)
    
    graph = workflow.compile()
    return graph

if __name__ == "__main__":
    
    graph = construct_super_graph()
    # for event in graph.stream(
    #     {"messages": [{"role": "user", "content": "How many cloudwatch logs do we have?"}]}
    # ):
    #     print(event)

    plan_str = """Step 1: Query_Cloudwatch to retrieve the error logs for the Glue job 'StockDataTransformation' on February 28, 2025. 
      Step 2: Query_Internal_Docs_and_web to understand the error message retrieved from Cloudwatch logs and find potential solutions or fixes.
      Step 3: Retrieve_App_Code for the Glue job 'StockDataTransformation' to review the current implementation and identify where the error might be occurring.
      Step 4: Based on the error analysis and potential solutions, modify the retrieved application code to fix the identified issue."""
    task = "Step 3: Retrieve_App_Code for the Glue job 'StockDataTransformation' to review the current implementation and identify where the error might be occurring."
    test_prompt = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {task}."""
    
    messages = graph.invoke(
        {"messages": [{"role": "user", "content": test_prompt}]}
    )
    print(messages)




