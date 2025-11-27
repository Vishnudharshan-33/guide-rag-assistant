"""
1C Portal RAG Chatbot - Main Application
Interactive chatbot for querying the 1C Portal Support Guide
"""

import os
import sys
from datetime import datetime
from ask_questions import ask_question, load_vector_database
from config import *


def print_banner():
    """Print welcome banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🤖 1C PORTAL SUPPORT CHATBOT                          ║
║           Powered by RAG + OpenAI GPT                        ║
║                                                              ║
║     Your AI assistant for Cognizant 1C Portal queries        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help information"""
    help_text = """
📚 AVAILABLE COMMANDS:
   • Type your question naturally (e.g., "How do I fill timesheet?")
   • 'help' or '?' - Show this help message
   • 'info' - Show database statistics
   • 'examples' - Show example questions
   • 'clear' - Clear screen
   • 'quit', 'exit', 'bye', 'q' - Exit the chatbot

💡 TIPS:
   • Be specific in your questions
   • Use keywords like "timesheet", "leave", "expense", "project"
   • Ask step-by-step questions for processes
   • Mention specific scenarios for better answers

📋 TOPICS COVERED:
   • Timesheet Management
   • Leave Applications
   • Expense Claims & Reimbursements
   • Project Assignments
   • Performance Management
   • Learning & Development
   • Security & Troubleshooting
"""
    print(help_text)


def print_examples():
    """Print example questions"""
    examples = """
💡 EXAMPLE QUESTIONS:

📊 Timesheet Related:
   • "How do I submit my weekly timesheet?"
   • "What should I do if my project code is not showing?"
   • "How to fill timesheet for overtime hours?"
   • "How do I correct a submitted timesheet?"

🏖️ Leave Related:
   • "How many leave days am I entitled to?"
   • "What is the process to apply for leave?"
   • "How do I check my leave balance?"
   • "Can I cancel an approved leave?"

💰 Expense Related:
   • "How do I submit an expense claim?"
   • "What documents are required for reimbursement?"
   • "What is the per diem rate for travel?"
   • "How long does reimbursement take?"

📁 Project Related:
   • "How do I request a project extension?"
   • "Where can I view my current allocations?"
   • "What should I do during bench time?"

🔧 Technical Issues:
   • "My timesheet is not submitting, what should I do?"
   • "How do I reset my 1C Portal password?"
   • "I cannot login to the portal"
"""
    print(examples)


def print_info():
    """Print database information"""
    index, chunks, metadata, total_pages = load_vector_database()

    if index is None:
        print("❌ Database not loaded")
        return

    info = f"""
📊 DATABASE STATISTICS:
   • PDF Document: 1C Portal Support Guide
   • Total Pages: {total_pages}
   • Total Chunks: {len(chunks)}
   • Vector Dimensions: 1536
   • Embedding Model: {EMBEDDING_MODEL}
   • Chat Model: {CHAT_MODEL}
   • Average Chunks per Page: {len(chunks) / total_pages:.1f}
   • Vector Index: {os.path.getsize(VECTOR_INDEX_PATH) / 1024:.1f} KB
   • Chunks Data: {os.path.getsize(CHUNKS_PKL_PATH) / 1024:.1f} KB
"""
    print(info)


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    """Main chatbot loop"""

    # Check if vector database exists
    if not os.path.exists(VECTOR_INDEX_PATH) or not os.path.exists(CHUNKS_PKL_PATH):
        print("❌ ERROR: Vector database not found!")
        print("\n📋 SETUP REQUIRED:")
        print("   1. Place your PDF in the 'data' folder")
        print("   2. Run: python pdf_to_vectors.py")
        print("   3. Then run: python rag_chatbot.py")
        print("\n💡 After setup, the chatbot will be ready to answer your questions!")
        return

    # Load database and show banner
    clear_screen()
    print_banner()

    print("🔄 Loading vector database...")
    index, chunks, metadata, total_pages = load_vector_database()

    if index is None:
        print("❌ Failed to load database. Please check setup.")
        return

    print(f"✅ Ready! Database loaded with {total_pages} pages and {len(chunks)} chunks")
    print("\n💬 Start asking questions about the 1C Portal!")
    print("💡 Type 'help' for commands or 'examples' for sample questions")
    print("=" * 70)

    # Chat loop
    conversation_count = 0

    while True:
        try:
            # Get user input
            print()
            question = input("👤 You: ").strip()

            # Handle empty input
            if not question:
                print("⚠️  Please enter a question!")
                continue

            # Handle commands
            if question.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Thank you for using 1C Portal Support Chatbot!")
                print(f"📊 You asked {conversation_count} questions in this session.")
                print("💡 Have a great day!")
                break

            elif question.lower() in ['help', '?']:
                print_help()
                continue

            elif question.lower() == 'info':
                print_info()
                continue

            elif question.lower() == 'examples':
                print_examples()
                continue

            elif question.lower() == 'clear':
                clear_screen()
                print_banner()
                continue

            # Process question
            conversation_count += 1
            print(f"\n🔍 Searching knowledge base...")

            answer, sources = ask_question(question, show_debug=False)

            if answer:
                print(f"\n🤖 Assistant:\n{answer}")

                if sources:
                    print(f"\n📄 Reference: Pages {', '.join(map(str, sources))} of the 1C Portal Support Guide")

                # Optional: Save conversation to log
                # log_conversation(question, answer, sources)
            else:
                print("\n❌ Sorry, I couldn't generate an answer. Please try rephrasing your question.")

        except KeyboardInterrupt:
            print("\n\n👋 Chatbot interrupted. Goodbye!")
            break

        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try again or type 'quit' to exit.")


if __name__ == "__main__":
    main()