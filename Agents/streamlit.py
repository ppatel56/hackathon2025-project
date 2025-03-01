import streamlit as st
import asyncio
from planning_agent import construct_plan_graph
import graphviz

# Initialize the planning agent
app = construct_plan_graph()

# Streamlit app
st.title("AWS Glue Developer Troubleshooting Agent Chat Interface")

# Input form
with st.form(key='query_form'):
    user_input = st.text_input("Enter your question:")
    submit_button = st.form_submit_button(label='Submit')

# Display the response
if submit_button and user_input:
    procesing_placeholder = st.empty()

    with st.expander("Final Response"):
        final_response_placeholder = st.empty()

    # Create an expander for the workflow output
    with st.expander("Thoughts"):
        workflow_placeholder = st.empty()

    procesing_placeholder.markdown("Thinking...")  # Highlight the current step

    #long running task, with interim update messages to be accumulated in response_placeholder
    async def main():
        config = {"recursion_limit": 50}
        inputs = {"input": user_input}
        step_trace = ""
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                step = k
                print("="*100)
                print("Step: ", step)
                sep = "="*70
                stage = f"### Stage: {step}"
                if "past_steps" in v:
                    details_item_1 = v["past_steps"][-1][0]
                    details_item_2 = v["past_steps"][-1][1]
                    details = f"#### Executed Step:\n{details_item_1}\n\n#### Response:\n{details_item_2}"
                    step_trace += f"{stage}\n\n{details}\n\n{sep}\n\n"
                if "plan" in v:
                    plan = v["plan"]
                    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
                    step_trace += f"{stage}\n\n{plan_str}\n\n{sep}\n\n"
                workflow_placeholder.markdown(step_trace)
        return v


    v = asyncio.run(main())
    procesing_placeholder.markdown("Processing done!")
    final_response_placeholder.markdown(f"### Final Response:\n{v['response']}")  # Highlight the final response




# Manually construct the graph
# def visual_graph():
#     dot = graphviz.Digraph(format='png')
#     dot.node('START', 'Start')
#     dot.node('planner', 'Planner')
#     dot.node('agent', 'Agent')
#     dot.node('replan', 'Replan')
#     dot.node('END', 'End')

#     dot.edge('START', 'planner')
#     dot.edge('planner', 'agent')
#     dot.edge('agent', 'replan')
#     dot.edge('replan', 'agent')
#     dot.edge('replan', 'END')

#     return dot

# graph = visual_graph()
# graph.render('graph', format='png', cleanup=True)
# st.image('graph.png', caption='Workflow Graph', use_column_width=True)
