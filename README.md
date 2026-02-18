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
