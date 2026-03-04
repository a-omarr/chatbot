# Backend (FastAPI)

## Quick start

```bash
# from project root
cd backend
python -m venv .venv
.venv\\Scripts\\activate  # On Windows
pip install --upgrade pip
pip install -r requirements.txt

# run dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000/docs` for the interactive API docs.

## Project layout

- `main.py`: FastAPI app entrypoint
- `api/v1/`: Versioned API routers
  - `router.py`: Root API router for v1
  - `chat_router.py`: Chatbot endpoint (`POST /api/v1/bot/chat`)
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment variables
- `.gitignore`: Backend-specific ignores
