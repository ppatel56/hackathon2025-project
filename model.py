import streamlit as st
import boto3
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from duckduckgo_search import DDGS
import re
import json

bedrock_client = boto3.client("bedrock-runtime", region_name = "us-east-1")

def call_bedrock(model_id, prompt):
    response = bedrock_client.invoke_model(
        ModelId = model_id,
        Body = json.dumps({"prompt": prompt, "max_tokens":1000, "temperature":0}),
        ContentType = 'application/jason',
        Accept ='application/json'
    )
    response_body = json.loads(response['Body'].read().decode('utf-8'))
    return response_body.get("outputs", [{}])[0].get("text", "No response from Bedrock")


# performs DuckDuckGo search, urls are extracted and status checked
# 
def ddg_search(query):
    results = DDGS().text(query, max_results=5)
    urls = []
    for result in results:
        url = result['href']
        urls.append(url)

    docs = get_page(urls)

    content = []
    for doc in docs:
        page_text = re.sub("\n\n+", "\n", doc.page_content)
        text = truncate(page_text)
        content.append(text)

    return content

# retrieves pages and extracts text by tag
def get_page(urls):
    loader = AsyncChromiumLoader(urls)
    html = loader.load()

    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["p"], remove_unwanted_tags=["a"])

    return docs_transformed

# helper function to reduce the amount of text
def truncate(text):
    words = text.split()
    truncated = " ".join(words[:400])

    return truncated

# create prompt for ollama

# create prompt for OpenAI
def create_prompt_bedrock(llm_query, search_results):

    prompt_start = (
        "Answer the question using only the context below.\n\n"+
        "Context:\n"
    )

    prompt_end = (
        f"\n\nQuestion: {llm_request}\nAnswer:"
    )

    prompt = (
        prompt_start + "\n\n---\n\n".join(search_results) + 
        prompt_end
    )

    return prompt

# use ollama with llama3 foundation model


# use openai's foundation models
def create_completion_openai(prompt):
    res = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        temperature=0,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    return res.choices[0].text


with st.form("prompt_form"):
    result =""
    prompt = ""
    search_query = st.text_area("DuckDuckGo search:", None)
    llm_query = st.text_area("LLM prompt:", None)
    submitted = st.form_submit_button("Send")
    if submitted:
        search_results = ddg_search(search_query)
        # prompt = create_prompt_ollama(llm_query,search_results)
        prompt = create_prompt_bedrock(llm_query,search_results)
        # result = create_completion_ollama(prompt)
        result = call_bedrock(model_id = "anthropic.claude-v2", prompt = prompt)
    
    e = st.expander("LLM prompt created:")
    e.write(prompt)
    st.write(result)
