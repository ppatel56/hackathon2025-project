import streamlit as st
import requests

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
            response = call_langgraph_chatbot(error_description, time_of_occurrence)
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