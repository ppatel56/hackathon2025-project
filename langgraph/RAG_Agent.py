from langgraph.graph import StateGraph
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage, AIMessage
from typing import TypedDict, List, Annotated
import os
import boto3
import uuid

#setting aws credentials
AWS_ACCESS_KEY_ID="ASIA4IM3HJTCWRUXGURE"
AWS_SECRET_ACCESS_KEY="BPmoeWqcKBpPp7d7BZ1YU3tXpA+gBF/uEeoZIq/z"
AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEBwaCXVzLWVhc3QtMSJHMEUCIGefTMRC+lQbUGqkwAFL8RQajda6bcoaqPOAWRmviP+nAiEA2BIdOCQacikVJAbSODuV6/OFj1PQDljVsDZLtya4L4wqmQMIVRAAGgw4NDI2NzU5OTc4OTMiDD57C47LHvag/Bv2Myr2AlFs9+xJ/fs/zLb7JavkV68329Q3ccFb48xF9hqFu5gBcSCp2aTKZyDfuhmZlD5V99nYxNA7hKP39AvcfpHS0HP2cUIPpdz5W8XFuohJES+pNlHYkr3zDgjdmXayb8w9fW9DC5TQqJ8dTgYLDQC52/Josy0oTnhN0b1XX1ArHumR19oZYU0poz7MIF5o/FSGyDDQKR1TQAwd5KJS9Tk1FUwNpfLsRtlakpzKP+0RTEWc0XlmM6CGeSYmhXAr7SVJh6OEgHkRCUOe+Q7rDIA4UeoPlSpeXqAwHgQykhuyZq3jWiAszs2RR/CsCUgL59M0cA7+vodUj0nmYFkJNEyDkX63DB/u/Frcc1lN4NzY4lpQAL53zW7tnM5qJzvEynJXwvXqj/IscVSFwT4QOsOwH1CjUu21VQ9IAs1yNTreEnf4qZy8V5yOzMPleQm6uNVAdBi4x5IOe2Np42NmzqWIVzrqFux1tQOHvNHqVEJ7eJTHD1j237b9MLWg+r0GOqYByO4S/Ub8UWkDfTs18hQS2lMaYkuQp2KBveOF3ixSgjHWrmZIxLVPG9IBWHflBeuYU8jhbYN+s4fYO8ezQ6XGftF6J9X/u2O4XMRVFjTrOI7dIbcOVOlKodMu2Cqtxw4FSZ589MEAnVTF6SSAdYiSrqMMM5KJMJMPMTHJO9Qn7kyEtLZoXP34zBAWo1gO2YwvhfYDxBrlcwtVeIzxJoXAUAm/sCmxIQ=="
## Create bedrock inference profile
# Create a Bedrock client
# bedrock = boto3.client(
#     'bedrock',
#     aws_access_key_id = AWS_ACCESS_KEY_ID,
#     aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
#     aws_session_token = AWS_SESSION_TOKEN,
#     region_name = 'us-east-1'
#     )

# response = bedrock.list_foundation_models()

# for model in response['modelSummaries']:
#     print(f"Model ARN: {model['modelArn']}")
#     # print(f"Supported Inference Types: {model['inferenceTypesSupported']}")
#     print("---")


##Test langgraph bedrock invokemodel call
## We will be using nova-pro model since claude models are severly rate limited in VG ephemeral account quotas (limited to 1 request per minute max for Sonnet)
llm = ChatBedrock(
    model_id='amazon.nova-pro-v1:0',  # or another available model
    model_kwargs=dict(temperature=0),
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN,
    region_name = 'us-east-1',
    provider = 'anthropic'
)
messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
print(ai_msg)



