# NotebookLM Clone

A RAG-powered document Q&A application similar to Google's NotebookLM, built with Flask and Gemini API.

## Features

- Upload and process text and PDF documents
- Question-answering based on document content
- Semantic search using vector embeddings
- Responsive UI with chat interface

## Technology Stack

- **Backend**: Flask, LangChain, FAISS
- **AI Model**: Google's Gemini 2.0 Flash
- **Embeddings**: HuggingFace Sentence Transformers
- **Frontend**: HTML, CSS, JavaScript
- **Document Processing**: PyPDF2 for PDF extraction

## Installation

1. Clone this repository:
```
git clone https://your-repository-url/NotebookLMClone.git
cd NotebookLMClone
```

2. Install required packages:
```
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Create a `.env` file in the root directory
   - Add your Gemini API key: `GEMINI_API_KEY=your_api_key_here`

## Usage

1. Start the Flask application:
```
python app/app.py
```

2. Open your browser and navigate to `http://127.0.0.1:5000/`

3. Upload a text or PDF document

4. Start asking questions about the content of your document

## Project Structure

```
NotebookLMClone/
├── app/
│   ├── app.py                # Main Flask application
│   ├── templates/            # HTML templates
│   │   └── index.html        # Main page template
│   └── static/               # Static files
│       ├── css/
│       │   └── style.css     # CSS styles
│       └── js/
│           └── script.js     # Frontend JavaScript
├── data/                     # Uploaded documents storage
├── .env                      # Environment variables (create this file)
└── requirements.txt          # Project dependencies
```

## How It Works

1. **Document Processing**: When a document is uploaded, it's processed and split into chunks.
2. **Vector Embeddings**: Each chunk is converted into a vector embedding using HuggingFace Sentence Transformers.
3. **Storage**: These embeddings are stored in FAISS, a vector database.
4. **Retrieval**: When a question is asked, the system finds the most relevant chunks using similarity search.
5. **Generation**: Relevant chunks and the question are sent to Gemini API to generate an accurate response.

## Future Improvements

- Multi-document management
- Document metadata support
- Citation and source tracking
- Advanced document visualization
- Custom fine-tuning options

## License

MIT

---

Created by [Your Name]
