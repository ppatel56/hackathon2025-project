import streamlit as st
import asyncio
from planning_agent import construct_plan_graph
import graphviz
import time

st.set_page_config(layout="wide")

def display_workflow_graph(placeholder, current_step=None):
    # Create a graph using graphviz
    dot = graphviz.Digraph()

    # Define node styles
    node_styles = {
        "planner": {"color": "black", "style": "filled", "fillcolor": "#ffffff"},
        "agent": {"color": "black", "style": "filled", "fillcolor": "#ffffff"},
        "replan": {"color": "black", "style": "filled", "fillcolor": "#ffffff"},
        "START": {"color": "black", "style": "filled", "fillcolor": "#ffffff"},
        "END": {"color": "black", "style": "filled", "fillcolor": "#ffffff"},
    }

    # Set the color of the current step to green
    if current_step and current_step in node_styles:
        node_styles[current_step]["fillcolor"] = "#ccffcc"

    # Add nodes with styles
    for node, style in node_styles.items():
        dot.node(node, **style)

    # Add edges
    dot.edge("START", "planner")
    dot.edge("planner", "agent")
    dot.edge("agent", "replan")
    dot.edge("replan", "agent")
    dot.edge("replan", "END")

    # Render the graph to a file
    dot.render('graph', format='png', cleanup=True)

    # Display the graph image in the placeholder
    placeholder.image('graph.png', caption='Workflow Graph', width=160, use_container_width=False)  # Adjust the width as needed

# Initialize the planning agent
app = construct_plan_graph()

# Apply custom CSS to add top padding to col2
st.markdown(
    """
    <style>
    .col2-padding {
        padding-top: 145px; /* Adjust this value to add more or less padding */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create a two-column layout
col1, col2 = st.columns([2, 1])

# Create a placeholder for the graph image and make it sticky
with col2:
    st.markdown('<div class="col2-padding">', unsafe_allow_html=True)
    graph_placeholder = st.empty()
    display_workflow_graph(graph_placeholder, current_step="START")
    st.markdown('</div>', unsafe_allow_html=True)

with col1:
    # Streamlit app
    st.title("AWS Glue Developer Troubleshooting Agent Chat Interface")

    # Input form
    with st.form(key='query_form'):
        user_input = st.text_area("Enter your question:", height=100)
        submit_button = st.form_submit_button(label='Submit')

    # Display the response
    if submit_button and user_input:
        procesing_placeholder = st.empty()

        # Create an expander for the workflow output
        with st.expander("Thought steps"):
            workflow_placeholder = st.empty()

        with st.expander("Final Response"):
            final_response_placeholder = st.empty()

        procesing_placeholder.markdown("Thinking...")  # Highlight the current step

        # Long running task, with interim update messages to be accumulated in response_placeholder
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
                    stage = f"### Stage: <span class='green-text'>{step.upper()}</span>"
                    if "past_steps" in v:
                        details_item_1 = v["past_steps"][-1][0]
                        details_item_2 = v["past_steps"][-1][1]
                        details = f"#### Executed Step:\n{details_item_1}\n\n#### Response:\n{details_item_2}"
                        step_trace = f"{stage}\n\n{details}\n\n{sep}\n\n" + step_trace
                        time.sleep(2)
                    if "plan" in v:
                        plan = v["plan"]
                        plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
                        step_trace = f"{stage}\n\n{plan_str}\n\n{sep}\n\n" + step_trace
                        time.sleep(2)
                    workflow_placeholder.markdown(step_trace, unsafe_allow_html=True)
                    # Update the graph with the current step
                    display_workflow_graph(graph_placeholder, current_step=step)
            return v

        v = asyncio.run(main())
        procesing_placeholder.markdown("Processing done!")
        display_workflow_graph(graph_placeholder, current_step="END")
        final_response_placeholder.markdown(f"### Final Response:\n{v['response']}")  # Highlight the final response