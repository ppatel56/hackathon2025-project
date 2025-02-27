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
options = members + ['FINISH']

sup_system_prompt = f"""
You are an AWS Development Supervisor, tasked with managing a conversation between the following workers: {options}.

Given the following user request, respond with the worker to act next. Respond with FINISH when the question has been answered.

If the user specifically asks you where to search for the information, assign the specific worker to answer the questions.
1. If the user's question topic relates to cloudwatch logs or errors, assign the Query_Cloudwatch worker.
2. If the user's question topic relates to code, assign the Retrieve_App_Code worker.
3. If the user's question topic relates to internal documentation or web search, assign the Query_Internal_Docs_and_web worker.
4. Otherwise, assign the Query_Internal_Docs_and_web worker.

The selected worker will perform a task and respond with their results and status. Again, you must select one worker to respond.

If the question made by the user does not need an answer from your workers, respond with FINISH.

Once the question has been answered by either you or your workers, finish by responding with FINISH.

Examples:
1. User: How many cloudwatch logs do you have access to?
   Worker: Answer: There are 10 cloudwatch logs in the Glue logs and 10 in the Lambda logs, totaling 20 logs.
   Response: FINISH

2. User: Provide the code for one of our glue jobs.
   Worker: Here is the code for the glue job: ...
   Response: FINISH

3. User: What error did glue job 'X' encounter on 2023-01-01? Also what part of the code caused the error?
    Query_Cloudwatch worker: The glue job 'X' encountered error 'Y' on 2023-01-01.
    Retrieve_App_Code worker: This is the code for glue job 'X'
    Response: FINISH
    
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
    question_answer: str

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
    

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    print("-----------------")
    print("supervisor_node")
    messages = [
        {"role": "system", "content": sup_system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    print(response)
    goto = response["next"]
    final_response = ""
    if goto == "FINISH":
        goto = END
        messages = [
            {"role": "system", "content": synthesizer_prompt},
            ] + state["messages"]
        print("Messages for final_response: ", messages)
        final_response = llm.invoke(messages).content

    return Command(goto=goto, update={"next": goto, "final_response": final_response})

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
            goto="supervisor",
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
            goto="supervisor",
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
            goto="supervisor",
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

    test_prompt_1 = "How many cloudwatch logs do we have?"
    test_prompt_2 = "Give me the code for glue job Hackathon-Test-Glue-1.py"
    test_prompt_3 = "What is the pipeline architecture for facebook?"
    test_prompt_3 = "Compare facebooks pipeline architecture to my team's pipeline architecture please."
    
    messages = graph.invoke(
        {"messages": [{"role": "user", "content": test_prompt_3}]}
    )
    print("===")
    print(messages['final_response'])
    #if links and documents keys are present, print them
    if "documents" in messages:
        print("===")
        print(messages['documents'])
    if "links" in messages:
        print("===")
        print(messages['links'])
    print("===")




