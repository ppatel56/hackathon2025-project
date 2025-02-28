import streamlit as st
import asyncio
from planning_agent import construct_plan_graph

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
    response_placeholder = st.container()

    #long running task, with interim update messages to be accumulated in response_placeholder
    async def main():
        config = {"recursion_limit": 50}
        inputs = {"input": user_input}
        response = []
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                if k != "__end__":
                    if "plan" in v:
                        response.append(v)  # Convert dictionary to string
                        response_placeholder.write(str(v))
        return response,v

    response,v = asyncio.run(main())
    st.write("Response:")
    st.write(v["response"])  # Display the last response