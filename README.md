# Chatbot Project

Full-stack chatbot with **FastAPI** backend and **React + TypeScript + Tailwind CSS** frontend.  
Supports **English**, **Turkish**, **Arabic**, and **Russian** out of the box.

---

## 📋 Prerequisites

| Tool       | Version |
|------------|---------|
| Python     | 3.10+   |
| Node.js    | 18+     |
| npm        | 9+      |

---

## ⚡ Quick Start (both services)

The easiest way to run everything at once:

```bash
chmod +x start.sh
./start.sh
```

This starts both the backend (`:8000`) and frontend (`:5173`) and shuts them down together with `Ctrl+C`.

---

## 🔧 Manual Setup

### Backend

```bash
cd backend

# 1. Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env             # edit if needed

# 4. Run dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint       | URL                                       |
|----------------|--------------------------------------------|
| API Docs       | http://localhost:8000/docs                 |
| Health Check   | `GET`  http://localhost:8000/health        |
| Chat           | `POST` http://localhost:8000/api/v1/bot/chat |

**Example request:**

```json
{ "message": "Hello!", "language": "en" }
```

---

### Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Run dev server
npm run dev
```

Open http://localhost:5173 in your browser.

> API calls are automatically proxied to `http://localhost:8000` via `vite.config.ts`.

---

## 🧪 Running Tests

```bash
# From the project root:
export PYTHONPATH=$(pwd):$(pwd)/backend
source backend/.venv/bin/activate

# Run all tests
python3 -m pytest backend/tests/

# Run with verbose output
python3 -m pytest backend/tests/ -v
```

### What's tested

| Test                              | Description                                              |
|-----------------------------------|----------------------------------------------------------|
| `test_intent_prediction_scenarios`| All 9 intents classified correctly in EN, TR, AR, RU     |
| `test_chat_endpoint_responses`    | Correct answers returned for cybersecurity, careers, etc. |
| `test_language_mismatch_logic`    | Language mismatch warning triggered properly             |
| `test_fallback_behavior`          | Nonsense input handled gracefully                        |

---

## 📁 Project Structure

```
chatbot/
├── backend/
│   ├── api/v1/bot.py           # Chat endpoint & knowledge base
│   ├── app/ml/
│   │   ├── intent_classifier.py # TF-IDF + LogisticRegression model
│   │   ├── active_learning.py   # Active learning utilities
│   │   └── evaluate_intents.py  # Model evaluation tools
│   ├── tests/
│   │   └── test_bot_scenarios.py # Automated test suite
│   ├── main.py                  # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   └── src/components/Chat.tsx  # Main chat UI component
├── start.sh                     # One-command launcher
├── documentation.md             # Detailed architecture docs
└── README.md
```

---

## 🤖 Supported Intents

| Intent             | Description                                |
|--------------------|--------------------------------------------|
| `company_overview` | About Toros Yazılım, history, mission      |
| `services`         | Software development, consulting           |
| `products`         | KIYOS, AuthNAC, ARI KONAKLAMA             |
| `cybersecurity`    | MAKSCYBER SIEM, network security           |
| `business_clients` | Enterprise solutions, project quotes       |
| `public_sector`    | Government, on-premise, compliance         |
| `careers`          | Job applications, internships              |
| `contact`          | Phone, email, office location              |
| `employees`        | Team size, workforce info                  |
