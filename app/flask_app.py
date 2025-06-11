import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np
import os.path

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# Initialize vector store dictionary to store document embeddings for each session
vector_stores = {}

class RAGSystem:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    def process_document(self, text, session_id):
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create a unique persist directory for each session
        persist_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', f'chroma_{session_id}')
        
        # Create vector store
        vector_store = Chroma.from_texts(
            texts=chunks, 
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        # Save vector store for session
        vector_stores[session_id] = vector_store
        
        return len(chunks)
    
    def query(self, question, session_id):
        try:
            print(f"Processing query for session: {session_id}")
            print(f"Available sessions: {list(vector_stores.keys())}")
            
            if session_id not in vector_stores:
                print(f"Session {session_id} not found in vector_stores")
                return "Please upload a document first."
            
            # Get the persist directory for this session
            persist_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', f'chroma_{session_id}')
            
            # If the directory doesn't exist, it means no document has been processed
            if not os.path.exists(persist_directory):
                print(f"Persist directory does not exist: {persist_directory}")
                return "Please upload a document first."
                
            # Search for relevant documents
            vector_store = vector_stores[session_id]
            print(f"Searching for similar documents to: '{question}'")
            docs = vector_store.similarity_search(question, k=3)
            
            if not docs:
                print("No relevant documents found")
                return "Sorry, I couldn't find any relevant information in the document to answer your question."
            
            # Create context from relevant documents
            context = "\n\n".join([doc.page_content for doc in docs])
            print(f"Found {len(docs)} relevant chunks")
            
            # Generate response using Gemini
            prompt = f"""
            Answer the question based on the following context:
            
            Context:
            {context}
            
            Question: {question}
            """
            
            print("Sending request to Gemini API...")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key or api_key == "your_gemini_api_key_here":
                print("WARNING: Gemini API key not properly configured")
                return "ERROR: Gemini API key is not configured. Please check your .env file."
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            import traceback
            print(f"Error in RAG query: {str(e)}")
            print(traceback.format_exc())
            return f"An error occurred while processing your question: {str(e)}"

# Initialize RAG system
rag_system = RAGSystem()

@app.route('/')
def home():
    # Initialize session if not already present
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        text = ""
        if filename.endswith('.pdf'):
            # Extract text from PDF
            with open(filepath, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
        else:
            # Assume it's a text file
            with open(filepath, 'r', encoding='utf-8') as text_file:
                text = text_file.read()
        
        # Process document
        chunks_count = rag_system.process_document(text, session['session_id'])
        
        return jsonify({
            'success': True,
            'message': f'File uploaded and processed successfully. Created {chunks_count} chunks.',
            'chunks_count': chunks_count
        })

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    if 'session_id' not in session:
        return jsonify({'error': 'Session expired. Please refresh the page.'}), 400
    
    question = data['question']
    try:
        response = rag_system.query(question, session['session_id'])
        if not response:
            return jsonify({'error': 'No response generated'}), 500
        
        return jsonify({
            'answer': response
        })
    except Exception as e:
        import traceback
        print("Error in query:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': f'Error processing your question: {str(e)}'}), 500

if __name__ == '__main__':
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
