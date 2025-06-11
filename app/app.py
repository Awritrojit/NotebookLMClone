import os
import uuid
import streamlit as st
import PyPDF2
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    st.error("ERROR: Gemini API key is not configured. Please check your environment variables.")
    st.stop()
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# Initialize session states
if 'vector_stores' not in st.session_state:
    st.session_state['vector_stores'] = {}
if 'files_uploaded' not in st.session_state:
    st.session_state['files_uploaded'] = {}
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

st.title("NotebookLMClone")

# Clean up function for vector stores
def cleanup_unused_stores():
    data_dir = "data"
    if os.path.exists(data_dir):
        for item in os.listdir(data_dir):
            if item.startswith("chroma_"):
                path = os.path.join(data_dir, item)
                file_id = item.replace("chroma_", "")
                if os.path.isdir(path) and file_id not in st.session_state['vector_stores']:
                    import shutil
                    shutil.rmtree(path)

# Sidebar for document management
with st.sidebar:
    st.header("Document Management")
    uploaded_files = st.file_uploader(
        "Upload PDF or TXT files", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_id = str(uuid.uuid4())
            
            # Process only if file hasn't been uploaded before
            if uploaded_file.name not in st.session_state['files_uploaded']:
                st.session_state['files_uploaded'][uploaded_file.name] = file_id
                persist_directory = os.path.join("data", f"chroma_{file_id}")
                os.makedirs(persist_directory, exist_ok=True)
                
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    text = ""
                    if uploaded_file.name.endswith('.pdf'):
                        pdf_reader = PyPDF2.PdfReader(uploaded_file)
                        for page in pdf_reader.pages:
                            text += page.extract_text()
                    else:
                        text = uploaded_file.read().decode('utf-8')

                    # Split and embed
                    embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000, 
                        chunk_overlap=100
                    )
                    chunks = text_splitter.split_text(text)
                    
                    # Create vector store for this file
                    vector_store = Chroma.from_texts(
                        texts=chunks,
                        embedding=embeddings,
                        persist_directory=persist_directory
                    )
                    
                    # Store in session state
                    st.session_state['vector_stores'][file_id] = {
                        'store': vector_store,
                        'name': uploaded_file.name,
                        'chunks': len(chunks)
                    }
                    st.success(f"✅ {uploaded_file.name} processed ({len(chunks)} chunks)")
    
    # Display currently loaded documents
    if st.session_state['files_uploaded']:
        st.markdown("---")
        st.subheader("Loaded Documents")
        for filename, file_id in st.session_state['files_uploaded'].items():
            if file_id in st.session_state['vector_stores']:
                doc_info = st.session_state['vector_stores'][file_id]
                st.markdown(f"📄 **{filename}** ({doc_info['chunks']} chunks)")
        
        if st.button("Clear All Documents"):
            st.session_state['vector_stores'] = {}
            st.session_state['files_uploaded'] = {}
            st.session_state['chat_history'] = []
            cleanup_unused_stores()
            st.rerun()

# Main chat interface
st.header("Chat with your Documents")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if question := st.chat_input("Ask a question about your documents..."):
    if not st.session_state['vector_stores']:
        st.warning("Please upload at least one document first.")
    else:
        # Display user message
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state.chat_history.append({"role": "user", "content": question})
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching through documents..."):
                try:
                    # Search across all loaded documents
                    all_relevant_docs = []
                    source_docs = {}
                    
                    for file_id, store_info in st.session_state['vector_stores'].items():
                        docs = store_info['store'].similarity_search(question, k=2)
                        if docs:
                            all_relevant_docs.extend(docs)
                            # Track which document each chunk came from
                            for doc in docs:
                                source_docs[doc.page_content] = store_info['name']
                    
                    # Sort by relevance (assuming the first results from each search are most relevant)
                    all_relevant_docs = all_relevant_docs[:3]
                    
                    if not all_relevant_docs:
                        response_text = "Sorry, I couldn't find any relevant information in the documents to answer your question."
                    else:
                        # Create context with source attribution
                        context_parts = []
                        for doc in all_relevant_docs:
                            source = source_docs[doc.page_content]
                            context_parts.append(f"From '{source}':\n{doc.page_content}")
                        context = "\n\n".join(context_parts)
                        
                        prompt = f"""
                        Answer the question based on the following context from multiple documents.
                        Include relevant source document names in your answer.
                        
                        Context:
                        {context}
                        
                        Question: {question}
                        """
                        
                        response = model.generate_content(prompt)
                        response_text = response.text
                    
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
                except Exception as e:
                    error_text = f"An error occurred: {str(e)}"
                    st.error(error_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": f"❌ {error_text}"})
