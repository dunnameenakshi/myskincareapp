import os
from google import genai
import chromadb
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key= GEMINI_API_KEY)


def search_knowledge_base(query,top_k=3):
    base_dir = os.path.dirname(__file__)
    chroma_path = os.path.join(base_dir,"chromadb")
    chroma_client = chromadb.PersistentClient(path = chroma_path)
    
    query_embedding = client.models.embed_content(
        model="gemini-embedding-2",
        contents=query
    ).embeddings[0].values
    
    collection = chroma_client.get_or_create_collection(name="skincare_knowledge")
    results = collection.query(query_embeddings=[query_embedding],n_results=top_k)
    if results and results['documents']:
        chunks = results['documents'][0]
        formatted = "\n\n".join([f"- {chunk}" for chunk in chunks])
        return formatted
    return ""