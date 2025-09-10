"""
One-Time Vector Store Builder Script.

This script processes all PDF documents found in the `knowledge_base` directory,
splits them into manageable text chunks, generates embeddings using Vertex AI,
and saves the result into a FAISS vector store on disk.

This process should be run whenever the knowledge base is updated. It is separate
from the main application to avoid the costly embedding process during runtime.

Usage:
    python scripts/build_vector_store.py
"""
import sys
from pathlib import Path
import time

# Add the project root to the Python path to allow for absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from tqdm import tqdm

# Import configurations and the embedding model client from the core application
from src.securemed_chat.core.llm import embeddings
from config import KNOWLEDGE_BASE_DIR, VECTOR_STORE_PATH, CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE

def build_vector_store():
    """
    Builds and saves a FAISS vector store from PDF documents.
    """
    print("🚀 Starting the vector store build process...")
    start_time = time.time()

    # 1. Load PDF Documents
    print(f"📂 Loading documents from '{KNOWLEDGE_BASE_DIR}'...")
    pdf_files = list(KNOWLEDGE_BASE_DIR.glob("*.pdf"))

    if not pdf_files:
        print("❌ CRITICAL ERROR: No PDF files found. Please add your medical guideline PDFs to the 'knowledge_base' directory.")
        return

    print(f"Found {len(pdf_files)} PDF files to process.")
    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        try:
            loader = PyPDFLoader(str(pdf_file))
            docs = loader.load_and_split(text_splitter=text_splitter)
            all_chunks.extend(docs)
        except Exception as e:
            print(f"⚠️ Warning: Error processing {pdf_file.name}: {e}")

    if not all_chunks:
        print("❌ CRITICAL ERROR: No text chunks were generated from the PDFs. Cannot build vector store.")
        return

    print(f"\n✅ Successfully created {len(all_chunks)} text chunks.")

    # 2. Create Vector Store with Batch Embeddings
    print(f"🧠 Creating new vector store with {len(all_chunks)} chunks using Vertex AI...")
    try:
        # Create the initial vector store from the first batch
        vector_store = FAISS.from_documents(documents=all_chunks[:BATCH_SIZE], embedding=embeddings)

        # Add the remaining documents in subsequent batches
        remaining_docs = all_chunks[BATCH_SIZE:]
        for i in tqdm(range(0, len(remaining_docs), BATCH_SIZE), desc="Embedding document batches"):
            batch = remaining_docs[i:i + BATCH_SIZE]
            if batch:
                vector_store.add_documents(batch)

        # Save the completed vector store to disk
        vector_store.save_local(VECTOR_STORE_PATH)
        end_time = time.time()
        print(f"\n✅ New vector store created and saved to '{VECTOR_STORE_PATH}'.")
        print(f"⏰ Total time taken: {end_time - start_time:.2f} seconds.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to create vector store: {e}")

if __name__ == "__main__":
    build_vector_store()
