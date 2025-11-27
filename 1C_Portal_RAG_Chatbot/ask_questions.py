"""
Question Answering Module
Handles querying the vector database and generating answers
"""


import faiss
import openai
import numpy as np
import pickle
import os
from config import *

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


def load_vector_database():
    """
    Load the vector database and chunks

    Returns:
        index: FAISS index
        chunks: list of text chunks
        metadata: chunk metadata
        total_pages: number of pages in original PDF
    """

    # Check if vector files exist
    if not os.path.exists(VECTOR_INDEX_PATH) or not os.path.exists(CHUNKS_PKL_PATH):
        print("❌ Error: Vector database not found!")
        print("🔧 Please run 'pdf_to_vectors.py' first to create the database.")
        return None, None, None, None


    try:
        # Load FAISS index
        index = faiss.read_index(VECTOR_INDEX_PATH)

        # Load chunks and metadata
        with open(CHUNKS_PKL_PATH,'rb') as f:
            data = pickle.load(f)

        chunks = data['chunks']
        metadata = data['metadata']
        total_pages = data['total_pages']

        print(f"✅ Database loaded: {len(chunks)} chunks from {total_pages} pages")

        return index, chunks, metadata, total_pages


    except Exception as e:
        print(f"❌ Error loading database: {str(e)}")
        return None, None, None, None



def search_similar_chunks(question, index, chunks, metadata, top_k=TOP_K_RESULTS):
    """
    Search for similar chunks using semantic search

    Args:
        question: User's question
        index: FAISS index
        chunks: List of text chunks
        metadata: Chunk metadata
        top_k: Number of results to return

    Returns:
        relevant_chunks: List of relevant text chunks with metadata
    """

    try:
        # Get question embedding
        response = openai.Embedding.create(
            input= question,
            model= EMBEDDING_MODEL
        )

        query_vector= np.array(response['data'][0]['embedding']).reshape(1,-1).astype('float32')

        # Normalize query vector
        faiss.normalize_L2(query_vector)

        # Search similar chunks
        scores, index = index.search(query_vector, top_k)

        # Prepare results
        relevant_chunks = []
        for score, idx in zip(scores[0], index[0]):
            if idx < len(chunks):
                relevant_chunks.append({
                    'text': chunks[idx],
                    'page_number': metadata[idx]['page_number'],
                    'similarity_score': float(score),
                    'chunk_index': idx
                })

        return relevant_chunks

    except Exception as e:
        print(f"❌ Error searching chunks: {str(e)}")
        return []

def generate_answer(question, relevant_chunks, total_pages):
    """
    Generate answer using GPT with relevant context

    Args:
        question: User's question
        relevant_chunks: List of relevant chunks with metadata
        total_pages: Total pages in document

    Returns:
        answer: Generated answer
        sources: List of source page numbers
    """

    try:
        # Build context from relevant chunks
        context_parts = []
        source_pages = set()

        for chunk_info in relevant_chunks:
            page_num = chunk_info['page_number']
            chunk_text = chunk_info['text']
            score = chunk_info['similarity_score']

            # Only include chunks with reasonable similarity
            if score > 0.5: # Threshold for relevance
                context_parts.append(f"[Page {page_num}] :\n{chunk_text}]")
                source_pages.add(page_num)

        if not context_parts:
            return "I couldn't find relevant information in the 1C Portal Support Guide to answer this question. Please try rephrasing or ask about topics covered in the guide (Timesheets, Leave Management, Expense Claims, Project Assignments, etc.).", []

        context = '\n\n---\n\n'.join(context_parts)

        # Generate answer using GPT
        response = openai.ChatCompletion.create(
            model = CHAT_MODEL,
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""Document Context (from 1C Portal Support Guide - {total_pages} pages total): {context}
                    User Question: {question}
                    Please provide a detailed answer based on the context above. Include specific steps if the question is about a process. Mention relevant page numbers when providing information."""
                }
            ],
            temperature = 0.7,
            max_tokens = 800
        )

        answer = response.choices[0].message.content
        sources = sorted(list(source_pages))

        return answer, sources

    except Exception as e:
        print(f"❌ Error generating answer: {str(e)}")
        return f"Sorry, I encountered an error while generating the answer: {str(e)}", []


def ask_question(question, show_debug=False):
    """
    Main function to ask a question and get an answer

    Args:
        question: User's question
        show_debug: Whether to show debug information

    Returns:
        answer: Generated answer
        sources: Source page numbers
    """

    # Load database
    index, chunks, metadata, total_pages = load_vector_database()

    if index is None:
        return None, []

    # Search for relevant chunks
    if show_debug:
        print(f"\n🔍 Searching for relevant information...")

    relevant_chunks = search_similar_chunks(question, index, chunks, metadata)

    if show_debug:
        print(f"📊 Found {len(relevant_chunks)} relevant chunks:")
        for i, chunk_info in enumerate(relevant_chunks[:3], 1):
            print(f"   {i}. Page {chunk_info['page_number']} (Score: {chunk_info['similarity_score']:.3f})")

    # Generate answer
    if show_debug:
        print(f"\n💭 Generating answer...")

    answer, sources = generate_answer(question, relevant_chunks, total_pages)

    return answer, sources


if __name__ == "__main__":
    # Test mode
    print("🧪 Testing ask_questions module...")

    test_question = "How do I fill my timesheet?"
    print(f"\n❓ Test Question: {test_question}")

    answer, sources = ask_question(test_question, show_debug=True)

    if answer:
        print(f"\n🤖 Answer:\n{answer}")
        if sources:
            print(f"\n📄 Sources: Pages {', '.join(map(str, sources))}")


