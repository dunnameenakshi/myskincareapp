import os
import PyPDF2
import chromadb
import logging
from google import genai
from dotenv import load_dotenv
logger = logging.getLogger('skincare')


load_dotenv()
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path,'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text+= extracted + "\n"
    return text

def split_into_chunks(text,chunk_size=800,overlapp=100):
    chunks = []
    start = 0
    while start<len(text):
        end = start+chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlapp
    return chunks

def get_embedding(client,text):
    result = client.models.embed_content(model ="gemini-embedding-2",
                                         contents = text)
    return result.embeddings[0].values

def ingest_pdf(pdf_filename="melasma_management.pdf"):
    base_dir = os.path.dirname(__file__)
    pdf_path = os.path.join(base_dir,"docs",pdf_filename)
    chroma_path = os.path.join(base_dir,"chromadb")
    logger.info(f"Reading pdf file : {pdf_filename}")
    text = extract_text_from_pdf(pdf_path)
    logger.info(f"Extracted {len(text)} characters")
    chunks = split_into_chunks(text)
    logger.info(f"Split into {len(chunks)} chunks")
    
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_or_create_collection(name="skincare_knowledge")

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(client, chunk)
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[f"melasma_{i}"]
        )
        print(f"  Stored chunk {i+1}/{len(chunks)}")

    print(f"Done! {len(chunks)} chunks stored in ChromaDB")
    
if __name__ == "__main__":
    ingest_pdf()
