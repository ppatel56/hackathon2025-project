from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
import boto3
from aws_creds import *

#Create Index
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]

docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
print(docs_list)

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)
doc_splits = text_splitter.split_documents(docs_list)

bedrock = boto3.client(
    'bedrock-runtime',
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    aws_session_token = AWS_SESSION_TOKEN,
    region_name = 'us-east-1'
    )

embeddings = BedrockEmbeddings(
    region_name="us-east-1",
    client = bedrock,
    model_id='amazon.titan-embed-text-v1'
)

# Add to vectorDB
vectorstore = FAISS.from_documents(
    documents=doc_splits,
    embedding=embeddings,
)

# Save the index to disk
vectorstore.save_local(folder_path="faiss_index",index_name='internal_team_docs')

retriever = vectorstore.as_retriever()