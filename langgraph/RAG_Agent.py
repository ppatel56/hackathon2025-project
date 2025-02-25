from langgraph.graph import StateGraph
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage, AIMessage
from typing import TypedDict, List, Annotated
import os
import boto3
import uuid

#setting aws credentials
AWS_ACCESS_KEY_ID="ASIA4IM3HJTC44CZRZUI"
AWS_SECRET_ACCESS_KEY="pxND7C8t07ETXdFdLVOpCDjnNUos0Li2/m9EypVc"
AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEBYaCXVzLWVhc3QtMSJGMEQCIHwaeQWSrU/BLakD7CVYa8E2tqpvyh7nIEbW4sdWH0i0AiB6QgrZz3Zp16M03BtxlpfhKGTGNO3gKUMdypH3eBpclCqZAwhOEAAaDDg0MjY3NTk5Nzg5MyIMR2h0OwoKHCSCDuD5KvYCQMK3no95VS2aClSM1xBhYTOmgqOfQWG5gFsjmIgsR8PrsYI4R1LTIkSTxzTb5mm4euE8P4C/TKmSX4xQ0WeBgSboUx83+ID+HPchsvGW4cwZ9TbWUsDnMDRVih8TZhuvJkqwOo1wf+Sd3xRYQCOtYSThlpbbA+iezuHCOK2MTKAeyv79ia8Ir1po69Av7/MWY3Uf9lvHU5tYGxeU3FmI1kxp1HkQMtmhGSNH/CGRrmnFzd2SglCWW8hd4Ct7Ejp3Xci8Mr2QxBvRbJxX55+d4/21gjhgENYuGe42TYLDl2n6rnMIruNA/W66Ai+byg/qNefI5q8Ll+ga+2F8xKdn4vbmw/vR+ARTFTdSG+2sJB8XK7A6q8FBfUxd/J9FsKZ5avmdXZ0M30PvXk8T5RIo4hq9lwFkhJi29fDhR2qG+yLmZNOKb3pUbJaTb5RfGq1N9L6+yYbB6/DpgKUjCNEH6ugPadHesZtd7GKSY3PBAxwW2ZeDoA4wm+H4vQY6pwGnS3sTf9Xa5ko70E0KSqzhRPoROqaHiacpBhen4DhhYBOhMe0e8ImEf+fHEVx8rKxEPQIH7W8/FB39bjHx9stBvse7S19q/4EAP4rMtAdx1B2BWyLGzw4byOvMCpGMUK4uAntU/pNHS78pWXHkzuNgJ+HXJibQa0uPyfDiYbUGKUaO+nWuD5l8Rj7+RyGbvr8O5QYVl98Z/HTQgb4WC1YH25cvj2ZEvg=="

## Create bedrock inference profile
# Create a Bedrock client
bedrock = boto3.client(
    'bedrock',
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN,
    region_name = 'us-east-1'
    )

# response = bedrock.list_foundation_models(byInferenceType="ON_DEMAND")

# for model in response['modelSummaries']:
#     print(f"Model ID: {model['modelId']}")
#     print(f"Supported Inference Types: {model['inferenceTypesSupported']}")
#     print("---")

# Define the parameters for the inference profile
inference_profile_name = "GIFSHack2025Profile"
description = "Inference profile for GIFS 2025 hackathon Claude 3.7 Sonnet"
model_arn = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0"

# Create the inference profile
# response = bedrock.create_inference_profile(
#     inferenceProfileName=inference_profile_name,
#     description=description,
#     clientRequestToken=str(uuid.uuid4()),
#     modelSource={
#         'copyFrom': model_arn
#     },
#     tags=[
#         {
#             'key': 'Project',
#             'value': 'GIFSHack2025Profile'
#         },
#         {
#             'key': 'Department',
#             'value': 'GIFSAI'
#         }
#     ]
# )

# # Print the ARN of the created inference profile
# print(f"Inference Profile ARN: {response['inferenceProfileArn']}")

# profile_arn = response['inferenceProfileArn']

llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",  # or another available model
    model_kwargs=dict(temperature=0),
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN
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

git config --global user.email "saullopezvaldez@vangurd.com"
git config --global user.name "Saul Lopez Valdez"

