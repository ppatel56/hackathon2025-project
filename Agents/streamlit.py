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
    st.write("Processing your request...")
    steps_placeholder = st.empty()
    details_placeholder = st.empty()

    final_response_placeholder = st.empty()
    steps_placeholder.markdown("")  # Highlight the current step
    details_placeholder.markdown(f"")  # Display the details

    #long running task, with interim update messages to be accumulated in response_placeholder
    async def main():
        config = {"recursion_limit": 50}
        inputs = {"input": user_input}
        response = []
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                step = k
                step_output = v
                steps_placeholder.markdown(f"### Stage: {step}")  # Highlight the current step
                if "past_steps" in v:
                    details_item_1 = v["past_steps"][-1][0]
                    details_item_2 = v["past_steps"][-1][1]
                    details_placeholder.markdown(f"#### Executed Step:\n{details_item_1}\n\n#### Response:\n{details_item_2}")  # Display the details
        return response,v


    response,v = asyncio.run(main())
    steps_placeholder.markdown("")  # Highlight the current step
    details_placeholder.markdown(f"") 
    
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
