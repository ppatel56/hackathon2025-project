from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
import os


def create_index():

    # Specify the directory containing your local files
    local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

    # List all files in the directory
    file_paths = [os.path.join(local_dir, f) for f in os.listdir(local_dir) if f.endswith('.txt')]
    docs = []
    for file_path in file_paths:
        loader = TextLoader(file_path)
        doc = loader.load()[0]  # Assuming each file results in one document
        doc.metadata = {
            "tag": "internal_team_documentation",
            "title": os.path.basename(file_path)
        }
        docs.append(doc)

    print(f"Loaded {len(docs)} documents")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )
    doc_splits = text_splitter.split_documents(docs)

    # Add to vectorDB
    vectorstore = FAISS.from_documents(
        documents=doc_splits,
        embedding=OpenAIEmbeddings()
    )

    # Save the index to disk
    vectorstore.save_local('internal_team_docs_index')

    return vectorstore

def read_index():
    vectorstore = FAISS.load_local('internal_team_docs_index',embeddings=OpenAIEmbeddings(), allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()
    return retriever

if __name__ == "__main__":
    retriever = create_index()
    print("Index created")
    retriever = read_index()
    print("Index read")
    print(retriever.invoke('What is the pipeline architecture?')[1])