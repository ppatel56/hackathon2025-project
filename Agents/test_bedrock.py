from langgraph.graph import StateGraph
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage, AIMessage
from typing import TypedDict, List, Annotated
import os
import boto3
import uuid
from aws_creds import *

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
    region_name = 'us-east-1'
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



