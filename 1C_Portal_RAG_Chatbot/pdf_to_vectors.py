"""
PDF to Vector Database Converter
This script converts the 1C Portal Support Guide PDF into a searchable vector database
Run this ONCE to create the vector database
"""
import faiss
import openai
import PyPDF2
import numpy as np
import pickle
import os
from config import *

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

def pdf_to_vectors(pdf_path):
    """
        Convert PDF to vector embeddings and save to FAISS index

        Args:
            pdf_path: Path to the PDF file

        Returns:
            embeddings: numpy array of embeddings
            chunks: list of text chunks
        """
    print("="*70)
    print("📚 1C PORTAL RAG SYSTEM - VECTOR DATABASE CREATION")
    print("="*70)

    #Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: PDF file not found at {pdf_path}")
        print("📁 Please place your PDF in the 'data' folder")
        return None, None

    # Read PDF
    print(f"\n📄 Reading PDF: {pdf_path}")
    try:
        with open(pdf_path,"rb") as f :
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)

            # Extract text from each page
            page_texts = []
            for page_num, page in enumerate(pdf_reader.pages):
                print(f"   Reading page {page_num + 1}/{total_pages}...", end='\r')
                page_text = page.extract_text()
                page_texts.append({
                    "text": page_text,
                    "page_number": page_num + 1
                })

        # Combine all text
        full_text = '\n'.join([p['text'] for p in page_texts])

        print(f"\n✅ PDF read successfully!")
        print(f"📊 Total pages: {total_pages}")
        print(f"📊 Total characters: {len(full_text):,}")
        print(f"📊 Average chars/page: {len(full_text) // total_pages:,}")


    except Exception as e:
        print(f"❌ Error reading PDF: {str(e)}")
        return None, None


    # Create chunks with better context preservation
    chunks = []
    chunk_metadata = []

    # Smart chunking: preserve paragraphs when possible
    for page_info in page_texts:
        page_text = page_info['text']
        page_num = page_info['page_number']

        # Split page into chunks
        for i in range(0,len(page_text),CHUNK_SIZE - CHUNK_OVERLAP):
            chunk_text = page_text[i:i+CHUNK_SIZE]


            if len(chunk_text.strip()) > 50:  # Skip very small chunks
                chunks.append(chunk_text)
                chunk_metadata.append({
                    'page_number': page_num,
                    'chunk_index': len(chunks) - 1,
                    'char_start': i,
                    'char_end': i + len(chunk_text)
                })

    print(f"✅ Created {len(chunks)} chunks")
    print(f"📊 Average chunk size: {sum(len(c) for c in chunks) // len(chunks)} characters")


    # Get embeddings from OpenAI
    print(f"\n🔄 Generating embeddings using OpenAI ({EMBEDDING_MODEL})...")
    print("⏳ This may take a few minutes...")

    embeddings = []
    failed_chunks = 0

    for i,chunk in enumerate(chunks):
        try:
            print(f"   Processing chunk {i + 1}/{len(chunks)} ({(i + 1) / len(chunks) * 100:.1f}%)...", end='\r')

            response = openai.Embedding.create(
                input=chunk,
                model =EMBEDDING_MODEL
            )
            embeddings.append(response['data'][0]['embedding'])

        except Exception as e:
            print(f"\n⚠️  Warning: Failed to embed chunk {i + 1}: {str(e)}")
            failed_chunks +=1
            # Use zero vector as placeholder
            embeddings.append([0.0] * 1536)

    print(f"\n✅ Embeddings generated!")

    if failed_chunks > 0:
        print(f"⚠️  {failed_chunks} chunks failed to embed")

    # Create FAISS index
    print(f"\n🗂️  Creating FAISS vector index...")
    embeddings_array = np.array(embeddings).astype('float32')

    # Normalize vectors for better similarity search
    faiss.normalize_L2(embeddings_array)

    # Create index with inner product (cosine similarity for normalized vectors)
    index = faiss.IndexFlatIP(1536) # OpenAI embeddings are 1536 dimensions
    index.add(embeddings_array)

    print(f"✅ FAISS index created with {index.ntotal} vectors")

    # Create vector_db directory if it doesn't exist
    os.makedirs(os.path.dirname(VECTOR_INDEX_PATH),exist_ok=True)

    # Save to files
    print(f"\n💾 Saving vector database...")

    try:
        # Save FAISS index
        faiss.write_index(index, VECTOR_INDEX_PATH)
        print(f"✅ Saved: {VECTOR_INDEX_PATH}")

        # Save chunks and metadata
        with open(CHUNKS_PKL_PATH,"wb") as f:
            pickle.dump({
                'chunks' : chunks,
                'metadata' : chunk_metadata,
                'total_pages' : total_pages,
                'pdf_name' : os.path.basename(pdf_path),
                'embedding_model' :EMBEDDING_MODEL
            }, f)

        print(f"✅ Saved: {CHUNKS_PKL_PATH}")

    except Exception as e:
        print(f"❌ Error saving files: {str(e)}")
        return None, None

    # Summary
    print("\n" + "=" * 70)
    print("🎉 VECTOR DATABASE CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"📁 Files created:")
    print(f"   • {VECTOR_INDEX_PATH}")
    print(f"   • {CHUNKS_PKL_PATH}")
    print(f"\n📊 Statistics:")
    print(f"   • Total pages processed: {total_pages}")
    print(f"   • Total chunks created: {len(chunks)}")
    print(f"   • Vector dimensions: 1536")
    print(f"   • Index size: {index.ntotal} vectors")
    print(f"   • Average chunks per page: {len(chunks) / total_pages:.1f}")
    print("\n✅ You can now run 'rag_chatbot.py' to start chatting!")
    print("=" * 70)

    return embeddings_array,chunks


if __name__ == "__main__":
    # Convert PDF to vectors
    embeddings, chunks = pdf_to_vectors(PDF_PATH)

    if embeddings is not None:
        print("\n✨ Setup complete!")
        print("▶️  Next step: Run 'rag_chatbot.py' to start the chatbot")
    else:
        print("\n❌ Setup failed. Please check the errors above.")









