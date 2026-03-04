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

The project includes a unified test runner that executes both automated unit tests and exhaustive system sanity checks.

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### What's tested

| Test Level | Description | Tool |
|------------|-------------|------|
| **Unit** | Intent prediction accuracy & ML logic | `pytest` |
| **Integration**| API endpoint flow & Language detection | `pytest` |
| **System** | Exhaustive check of all topics in 4 languages | `system_test.py` |

For detailed testing documentation, see [TESTING_WORKFLOW.md](./TESTING_WORKFLOW.md).

---

## 📁 Project Structure

```
chatbot/
├── backend/
│   ├── api/v1/
│   │   ├── chat_router.py        # Chat endpoint & knowledge base wiring
│   │   └── router.py             # API router configuration
│   ├── app/ml/
│   │   ├── intent_engine.py      # TF-IDF + LogisticRegression intent model
│   │   ├── knowledge_engine.py   # Cross-lingual knowledge-base retrieval
│   │   ├── data_collector.py     # Active learning logging utilities
│   │   └── model_evaluator.py    # Model evaluation tools
│   ├── tests/
│   │   ├── test_bot_scenarios.py # Core ML intent tests
│   │   └── system_test.py        # Exhaustive multilingual system checks
│   ├── main.py                   # FastAPI app entry point
│   ├── requirements.txt
│   └── AGENT_ARCHITECTURE.md     # Detailed backend agent flow
├── frontend/
│   ├── src/components/Chat.tsx   # Main chat UI component
│   └── README.md
├── start.sh                      # One-command launcher
├── TESTING_WORKFLOW.md           # Testing and QA documentation
├── documentation.md              # High-level architecture docs
└── README.md
```

---

| Intent             | Description                                |
|--------------------|--------------------------------------------|
| `company_overview` | About Toros Yazılım, history, mission      |
| `services`         | Software development, consulting           |
| `products`         | KIYOS, AuthNAC, ARI KONAKLAMA             |
| `cybersecurity`    | MAKSCYBER SIEM, network security           |
| `business_clients` | Enterprise solutions, project quotes       |
| `public_sector`    | Government, on-premise, compliance         |
| `career_info`      | Job applications, internships              |
| `contact_info`     | Phone, email, office location              |
| `employees`        | Team size, workforce info                  |
| `greeting`         | Welcome messages and greetings             |
| `makscyber_siem`   | Specific SIEM product details              |
| `authnac_info`     | Specific Network Access Control details    |
| `identity_management`| Specific KIYOS/Identity solutions        |
| `custom_software`  | Bespoke development inquiries              |
| `it_consultancy`   | Technical advising and strategy            |
| `other`            | Fallback for unclassified messages         |
