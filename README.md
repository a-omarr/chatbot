# Chatbot Project

Full-stack chatbot starter with **FastAPI** backend and **React + TypeScript + Tailwind CSS** frontend.

## Project structure

- `backend/` – FastAPI application (API and business logic)
- `frontend/` – React + TypeScript + Tailwind UI (Vite)

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ and **npm** (or pnpm/yarn if you prefer and adjust commands)

On Windows, run commands in **PowerShell** or **cmd**.

---

## Backend (FastAPI)

Located in `backend/`.

### Install & run (development)

```bash
cd backend

# create and activate virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# run dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- Docs: `http://localhost:8000/docs`
- Health check: `GET http://localhost:8000/health`
- Chat endpoint: `POST http://localhost:8000/api/v1/bot/chat`

Example chat request body:

```json
{
  "message": "Hello!"
}
```

### Environment variables

Copy `.env.example` to `.env` in the `backend/` folder and customize as needed:

```bash
cd backend
copy .env.example .env
```

Update CORS origins there when you deploy to production.

---

## Frontend (React + TypeScript + Tailwind)

Located in `frontend/`.

### Install & run (development)

```bash
cd frontend

# install dependencies
npm install

# start dev server
npm run dev
```

The app will be available at: `http://localhost:5173`

During development, `/api/...` requests are proxied to `http://localhost:8000` (configured in `vite.config.ts`). That means if both servers are running, the chat UI will talk to your FastAPI backend automatically.

---

## Typical dev workflow

1. **Start backend**
   - In one terminal:
     ```bash
     cd backend
     .venv\Scripts\activate  # if not already
     uvicorn main:app --reload --host 0.0.0.0 --port 8000
     ```

2. **Start frontend**
   - In another terminal:
     ```bash
     cd frontend
     npm install   # first time only
     npm run dev
     ```

3. Open `http://localhost:5173` in your browser and start chatting.

---

## Production readiness notes

- **Backend**
  - Versioned routes under `api/v1/` for easier evolution.
  - CORS middleware configured; tighten `origins` for production.
  - Ready to plug in real chatbot logic inside `api/v1/bot.py`.

- **Frontend**
  - Vite + React + TypeScript with Tailwind configured via PostCSS.
  - Basic but modern chat UI layout, easily extendable.
  - ESLint configured for TypeScript + React.

You can now extend the bot logic, add authentication, persistence, or integrate with external LLM APIs as needed.
