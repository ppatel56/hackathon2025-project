import streamlit as st
import requests
import base64

# Function to tie the streamlit UI with the Agent
def call_langgraph_chatbot(error_description, time_of_occurrence=None, severity_level=None, uploaded_file=None):
    # Prepare the payload for the chatbot
    payload = {
        "error_description": error_description,
        "time_of_occurrence": time_of_occurrence,
        "severity_level": severity_level,
        "uploaded_file": None
    }
    
    # Handle the uploaded file
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            # Read text file
            file_content = uploaded_file.read().decode("utf-8")
            payload["uploaded_file"] = file_content
        elif uploaded_file.type in ["image/png", "image/jpeg"]:
            # Read image file and encode in base64
            file_content = base64.b64encode(uploaded_file.read()).decode("utf-8")
            payload["uploaded_file"] = file_content
    
    # Replace with your LangGraph chatbot API endpoint
    chatbot_url = "https://your-langgraph-chatbot-api.com/chat"
    
    try:
        # Send the request to the chatbot
        response = requests.post(chatbot_url, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Return the chatbot's response
        return response.json().get("response", "No response from chatbot.")
    except requests.exceptions.RequestException as e:
        return f"Error communicating with the chatbot: {e}"

# Title and welcome message
st.title("AI Production Support Chatbot")
st.write("Welcome! Describe your issue below to get help.")

# Inputs
error_description = st.text_area("Describe the error you're encountering:")
time_of_occurrence = st.text_input("When did the error occur? (Optional):")
severity_level = st.selectbox("Select the severity level:", ["Critical", "High", "Medium", "Low"])
uploaded_file = st.file_uploader("Upload logs or screenshots (Optional):", type=["txt", "log", "png", "jpg"])

# Chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Submit button
if st.button("Get Help"):
    if error_description:
        with st.spinner("Analyzing your issue..."):
            response = call_langgraph_chatbot(error_description, time_of_occurrence, severity_level, uploaded_file)
            st.session_state.chat_history.append({"user": error_description, "bot": response})
        
        st.write("### Chat History:")
        for chat in st.session_state.chat_history:
            st.write(f"**You:** {chat['user']}")
            st.write(f"**Bot:** {chat['bot']}")
            st.write("---")
    else:
        st.error("Please provide a description of the error.")

# Feedback
feedback = st.radio("Was this response helpful?", ["Yes", "No"])
if feedback:
    st.write("Thank you for your feedback!")

# Reset button
if st.button("Reset Form"):
    st.session_state.chat_history = []
    st.experimental_rerun()

