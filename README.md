# 🤖 Documentbase RAG Chatbot

A production-grade **Retrieval-Augmented Generation (RAG)** chatbot that allows multiple users to upload PDFs and chat with their documents using AI. Built with **FastAPI**, **Streamlit**, **PostgreSQL**, **ChromaDB**, and the **Groq API**.

## ✨ Features

- **Multi-user authentication** — JWT-based auth with per-user data isolation
- **PDF upload & processing** — Extract text, chunk, embed, and store vectors
- **RAG chat pipeline** — Retrieve relevant context and generate AI-powered answers
- **Chat history** — Persistent chat sessions and message history
- **Modular architecture** — Clean separation of concerns with SOLID principles

## 📁 Project Structure

```
rag_chatbot/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── core/
│   │   ├── config.py            # Environment configuration
│   │   ├── security.py          # JWT & password hashing
│   │   └── logging.py           # Logging configuration
│   ├── database/
│   │   ├── postgres.py          # Async DB connection
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── user_schema.py       # Auth request/response schemas
│   │   ├── chat_schema.py       # Chat request/response schemas
│   │   └── document_schema.py   # Document upload schemas
│   ├── repositories/
│   │   ├── user_repository.py   # User data access
│   │   └── chat_repository.py   # Chat data access
│   ├── services/
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── pdf_service.py       # PDF processing pipeline
│   │   ├── embedding_service.py # SentenceTransformer embeddings
│   │   ├── vector_service.py    # ChromaDB vector store
│   │   ├── llm_service.py       # Groq API integration
│   │   ├── rag_service.py       # RAG pipeline orchestration
│   │   └── chat_service.py      # Chat session management
│   ├── routers/
│   │   ├── auth_router.py       # POST /register, /login
│   │   ├── document_router.py   # POST /upload_pdf
│   │   ├── chat_router.py       # POST /chat
│   │   └── session_router.py    # GET /sessions, /messages
│   └── utils/
│       ├── text_splitter.py     # Recursive text chunking
│       └── helpers.py           # Utility functions
├── frontend/
│   └── streamlit_app.py         # Streamlit UI
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
└── README.md
```

## 🛠️ Prerequisites

- **Python 3.10+**
- **PostgreSQL** (running locally or remotely)
- **Groq API key** — [Get one here](https://console.groq.com/)

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
cd rag_chatbot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL

Create a database for the application:

```sql
CREATE DATABASE rag_chatbot;
```

### 5. Configure Environment Variables

Edit the `.env` file with your credentials:

```env
GROQ_API_KEY=your-groq-api-key-here
POSTGRES_DB_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/rag_chatbot
CHROMA_DB_PATH=./chroma_db
JWT_SECRET_KEY=your-strong-random-secret-key
```

### 6. Start the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger documentation.

### 7. Start the Frontend

In a separate terminal:

```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit UI will open at `http://localhost:8501`.

## 📡 API Endpoints

| Method | Endpoint                    | Description              | Auth     |
|--------|-----------------------------|--------------------------|----------|
| POST   | `/auth/register`            | Register a new user      | No       |
| POST   | `/auth/login`               | Login and get JWT token  | No       |
| POST   | `/documents/upload_pdf`     | Upload and process a PDF | Required |
| POST   | `/chat`                     | Ask a question (RAG)     | Required |
| GET    | `/sessions`                 | List chat sessions       | Required |
| GET    | `/sessions/messages/{id}`   | Get session messages     | Required |

## 🔧 Tech Stack

| Component     | Technology                |
|---------------|---------------------------|
| Backend       | FastAPI + Uvicorn         |
| Database      | PostgreSQL + SQLAlchemy   |
| Vector Store  | ChromaDB                  |
| Embeddings    | Sentence Transformers     |
| LLM           | Groq API (gpt-oss-120b)  |
| Auth          | JWT + bcrypt              |
| Frontend      | Streamlit                 |

## 📝 Usage

1. **Register** an account via the Streamlit UI or API
2. **Upload PDFs** — Documents are processed, chunked, and embedded
3. **Ask questions** — The RAG pipeline retrieves relevant context and generates answers
4. **View history** — Browse past chat sessions from the sidebar

## ⚠️ Production Notes

- Change `JWT_SECRET_KEY` to a strong random value
- Restrict CORS origins in `main.py`
- Use connection pooling for PostgreSQL
- Consider rate limiting for API endpoints
- Store uploaded PDFs in cloud storage (S3, GCS) for persistence
