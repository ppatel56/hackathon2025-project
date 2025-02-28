import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Union
from pydantic import BaseModel, Field
from typing import Literal
from langgraph.graph import END
from supervisor_agent import construct_super_graph
from langgraph.graph import StateGraph, START


#define the supervisor agent
supervisor = construct_super_graph()

##Planning Step

class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

workers = ['Query_Internal_Docs_and_web', 'Query_Cloudwatch', 'Retrieve_App_Code']
planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
    f"""Objective: Develop a step-by-step plan to solve the given problem using only the following task workers:

        Available Task Workers:
        1. Query_Internal_Docs_and_web: Search internal documentation and web resources for relevant information.
        2. Query_Cloudwatch: Query sql database containing glu job cloudwatch logs.
        3. Retrieve_App_Code: Fetch the code for the 'StockDataTransformation' Glue job.

        Instructions for Plan Creation:
        1. Use ONLY the task workers listed above.
        2. Each step must be actionable and executed by one of these workers.
        3. Ensure each step provides all necessary information for execution - avoid assumptions or skipped details.
        4. The plan should progress logically towards a final answer or solution.
        5. The final step should be an analysis of the completed previous steps to complete answer to the objective.
        6. Avoid any steps before final step that do not directly utilize one of the specified task workers.

        Plan Format:
        Step 1: [Task Worker] - [Specific action and expected outcome]
        Step 2: [Task Worker] - [Specific action and expected outcome]
        ...
        Final Step: [Analysis of previous step completions leading to final answer]

        Example Plan:
        Step 1: Query_Cloudwatch to retrieve the error logs for the Glue job 'StockDataTransformation' on February 28, 2025. 
        Step 2: Query_Internal_Docs_and_web to understand the error message retrieved from Cloudwatch logs and find potential solutions or fixes.
        Step 3: Retrieve_App_Code for the Glue job 'StockDataTransformation' to review the current implementation and identify where the error might be occurring.
        Step 4: Based on the queried error logs, the queried documentation, and the retirved application code, produce a proposed solution to the application error.

        Remember: Each step should be essential for reaching the solution. Eliminate any superfluous steps that don't contribute directly to achieving the objective."""
        ),
        ("placeholder", "{messages}"),
    ]
)
planner = planner_prompt | ChatOpenAI(
    model="gpt-4o", temperature=0
).with_structured_output(Plan)

##Replanning step

class Response(BaseModel):
    """Response to user."""

    response: str = Field(
        description="Response for final step: Analysis of previous step completions and proposed solution. Do not include an updated plan here."
    )


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user with proposed solution or answer, use Response. "
        "Provide your updated plan using Plan, listing only the remaining steps to be executed"
    )


replanner_prompt = ChatPromptTemplate.from_template(
    """Objective: {input}

Available Task Workers:
1. Query_Internal_Docs_and_web: Query internal documentation and web for information.
2. Query_Cloudwatch: Retrieve Glue job log information from CloudWatch.
3. Retrieve_App_Code: Fetch the code for the 'StockDataTransformation' Glue job.

Original Plan:
{plan}

Completed Steps:
{past_steps}

Instructions:
1. Review the objective, available task workers, original plan, and completed steps.
2. Create or update the plan using ONLY the specified task workers.
3. Each step must be actionable and executed by one of the task workers.
4. Do not include any steps that include task workers that have already been executed.
5. Do not include any steps that have already been completed.
6. Ensure the plan leads logically to a final answer or solution.
7. If you're at the final step, provide the proposed solution based on the completed steps.

Plan Format:
Step 1: [Task Worker] - [Specific action and expected outcome]
Step 2: [Task Worker] - [Specific action and expected outcome]
...
Final Step: [Analysis of previous step completions leading to final answer]

Example Plan:
Step 1: Query_Cloudwatch to retrieve the error logs for the Glue job 'StockDataTransformation' on February 28, 2025. 
Step 2: Query_Internal_Docs_and_web to understand the error message retrieved from Cloudwatch logs and find potential solutions or fixes.
Step 3: Retrieve_App_Code for the Glue job 'StockDataTransformation' to review the current implementation and identify where the error might be occurring.
Step 4: Based on the queried error logs, the queried documentation, and the retirved application code, produce a proposed solution to the application error.


Note: Ensure each step is necessary and directly contributes to achieving the objective. Avoid superfluous steps or those not utilizing the specified task workers."""
)


replanner = replanner_prompt | ChatOpenAI(
    model="gpt-4o", temperature=0
).with_structured_output(Act)

async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = await supervisor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }


async def plan_step(state: PlanExecute):
    plan = await planner.ainvoke({"messages": [("user", state["input"])]})
    return {"plan": plan.steps}


async def replan_step(state: PlanExecute):
    output = await replanner.ainvoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}


def should_end(state: PlanExecute):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"
    
def construct_plan_graph():
    workflow = StateGraph(PlanExecute)

    # Add the plan node
    workflow.add_node("planner", plan_step)

    # Add the execution step
    workflow.add_node("agent", execute_step)

    # Add a replan node
    workflow.add_node("replan", replan_step)

    workflow.add_edge(START, "planner")

    # From plan we go to agent
    workflow.add_edge("planner", "agent")

    # From agent, we replan
    workflow.add_edge("agent", "replan")

    workflow.add_conditional_edges(
        "replan",
        # Next, we pass in the function that will determine which node is called next.
        should_end,
        ["agent", END],
    )

    # Finally, we compile it!
    # This compiles it into a LangChain Runnable,
    # meaning you can use it as you would any other runnable
    app = workflow.compile()

    return app

if __name__ == "__main__":
    import asyncio

    objective = "please come up with a solution to the latest glue job error for StockDataTransformation job. Also, compare with solutions from the web to enhance your proposed solution"
    config = {"recursion_limit": 50}
    inputs = {"input": objective}
    app = construct_plan_graph()
    

    async def main():
        async for event in app.astream(inputs, config=config):
            response = []
            for k, v in event.items():
                print("="*100)
                print("Step: ", k)
                print("details: ", v)
                response.append(v)
                # if k != "__end__":
                    
        
        print("Final response: ", response)

    asyncio.run(main())
    

