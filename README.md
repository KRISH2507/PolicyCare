# AarogyaAid

An AI-powered health insurance recommendation platform that matches Indian users to the right policy based on their health profile, then lets them ask follow-up questions about it in plain language.

> **Demo:** [Add your Loom/video link here]  
> **Live:** Not deployed (local setup — see Quick Start below)

---

## Quick Start

```bash
# 1. Clone
git clone <your-repo-url>
cd aarogyaaid

# 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env           # fill in OPENAI_API_KEY and JWT_SECRET
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173

# 4. Upload sample policies
# Log in as admin → Admin dashboard → upload files from sample-data/

# 5. Run tests
cd backend
pytest tests/test_recommendation.py -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│  Landing → Login/Signup → Profile Form → Results + Chat     │
│                        Admin Dashboard                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ fetch + Bearer JWT
┌──────────────────────────▼──────────────────────────────────┐
│                      FastAPI Backend                         │
│  /api/auth    /api/recommend    /api/chat    /api/admin      │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
  SQLite DB      ChromaDB       OpenAI API     File System
  (users,        (policy        (gpt-4o-mini   (uploaded
   policies)      vectors)       embeddings)    documents)
```

**RAG Pipeline (on upload):**
```
PDF/TXT/JSON → PyMuPDF parse → sliding window chunks (300w, 50w overlap)
             → text-embedding-3-small → ChromaDB cosine store
```

**RAG Pipeline (on query):**
```
User profile → weighted query string → embed → ChromaDB top-K retrieve
             → GPT-4o-mini + system prompt + retrieved context → JSON response
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/login` | None | Login or auto-register |
| POST | `/api/recommend/` | User JWT | Get policy recommendation |
| POST | `/api/chat/` | User JWT | Chat about recommended policy |
| GET | `/api/admin/policies` | Admin JWT | List all policies |
| POST | `/api/admin/upload` | Admin JWT | Upload + vectorise policy |
| PATCH | `/api/admin/policies/{id}` | Admin JWT | Edit policy metadata |
| DELETE | `/api/admin/policies/{id}` | Admin JWT | Delete policy + vectors |
| GET | `/health` | None | Health check |

Full interactive docs: http://localhost:8000/docs

---

## What Makes This Different

Most AI assignment projects call an LLM with a hardcoded prompt and return whatever it says. AarogyaAid does three things that are harder to fake:

1. **Grounded output** — the LLM can only cite facts present in the uploaded documents. The system prompt explicitly forbids stating anything not in the retrieved context. Every factual claim in the response includes a source citation.

2. **Per-policy chat filtering** — the chat RAG retrieval uses a ChromaDB `where` clause to filter results to the recommended policy only. The user gets answers about their specific plan, not generic insurance information.

3. **Admin-driven knowledge base** — the recommendation quality improves as admins upload more policies. No code changes, no redeployment. This is the architecture that makes the product maintainable in production.

---

## Features

- **AI-grounded recommendations** — GPT-4o-mini reads only the actual uploaded policy documents (RAG) before recommending. No hallucinated premiums or coverage details.
- **Side-by-side policy comparison** — best-fit card plus peer alternatives with suitability scores.
- **Persistent explainer chat** — users can ask "what does co-pay mean for me?" and get answers grounded in the specific policy they were recommended.
- **Admin knowledge base** — admins upload PDF / JSON / TXT policy documents; the system parses, chunks, embeds, and stores them in ChromaDB automatically.
- **Secure JWT auth** — bcrypt-hashed passwords, 24-hour JWT tokens, role-based route protection (user vs admin).
- **Auto-registration** — new users are created on first login; no separate signup flow required on the backend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, React Router v7, plain CSS |
| Backend | FastAPI 0.136, Python 3.11 |
| Database | SQLite (dev) via SQLAlchemy 2.0 |
| Vector DB | ChromaDB 1.5 (local persistent) |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| PDF Parsing | PyMuPDF (fitz) |
| Auth | python-jose (JWT), passlib + bcrypt |

---

## Why This AI Framework Choice (vs Google ADK)

The assignment mentioned Google ADK as a reference. Here is why a direct OpenAI SDK + ChromaDB approach was chosen instead, and the honest tradeoffs.

### What was chosen
- **OpenAI Python SDK** called directly from FastAPI route handlers
- **ChromaDB** as a local persistent vector store
- **Custom RAG pipeline**: upload → parse → chunk → embed → store → retrieve → generate

### Why not Google ADK
Google ADK is an agent orchestration framework. It is well-suited for multi-step agentic workflows where an LLM decides which tools to call in sequence. For this product, that abstraction adds cost without benefit:

| Concern | Direct SDK | Google ADK |
|---|---|---|
| **Tool control** | Full control over every prompt, retrieval filter, and response schema | ADK manages tool dispatch; harder to enforce strict JSON output schemas |
| **Retrieval flexibility** | ChromaDB `where` clause filters by `policy_id` — chat is scoped to the recommended policy only | ADK retrieval tools are more generic; per-policy filtering requires custom tool wrappers |
| **Latency** | One embedding call + one completion call per request | ADK adds agent loop overhead (plan → act → observe) even for single-step tasks |
| **Structured output** | `response_format={"type": "json_object"}` enforces schema at the API level | ADK output parsing requires additional validation layers |
| **Maintainability** | The entire AI logic is in two ~100-line Python files | ADK introduces framework-specific abstractions that require ADK knowledge to debug |
| **Delivery speed** | No framework installation, no agent graph configuration | ADK setup and agent definition adds meaningful setup time |

**Honest tradeoff:** If the product needed multi-step reasoning (e.g., "compare three policies, then check if the user qualifies for a government scheme, then draft an application letter"), ADK's agent loop would be the right choice. For a two-step RAG pattern (retrieve → generate), it is unnecessary complexity.

---

## Recommendation Logic

The engine converts a 6-field user profile into a weighted semantic search query, retrieves the top-10 most relevant policy chunks from ChromaDB, then asks GPT-4o-mini to reason over them.

| Profile Field | How it influences matching |
|---|---|
| `full_name` | Used in the personalised `why_this_policy` explanation |
| `age` | Included in the retrieval query; LLM uses it to assess premium bands and entry age eligibility |
| `city_tier` | Metro users need higher room rent limits and broader hospital networks; query weighted accordingly |
| `lifestyle` | Active / Athlete profiles append OPD, sports injury, and wellness benefit keywords to the query |
| `pre_existing_conditions` | Appends "waiting period for pre-existing diseases" to the query; LLM is instructed to prioritise plans with shorter PED waiting periods |
| `income_band` | Low-income bands append affordability and low-premium keywords; high-income bands allow premium plans to surface |

The LLM is given a strict JSON output schema (via `response_format`) and a system prompt that forbids hallucination — it must cite the source document and page number for every factual claim.

---

## RAG Pipeline

```
Admin uploads file (PDF / JSON / TXT)
        │
        ▼
parser_service.py  →  extract text per page  →  List[{page, text}]
        │
        ▼
chunk_service.py   →  sliding window chunks  →  List[{text, page_number, chunk_index}]
        │              (300 words, 50-word overlap)
        ▼
vector_service.py  →  OpenAI text-embedding-3-small  →  List[float] per chunk
        │
        ▼
ChromaDB           →  store(ids, embeddings, metadatas, documents)
        │
        ▼
At query time:
  user profile  →  generate_query_from_profile()  →  query string
        │
        ▼
  embed query   →  ChromaDB cosine similarity search  →  top-K chunks
        │
        ▼
  GPT-4o-mini   →  system prompt + retrieved context + user profile  →  JSON response
```

If ChromaDB is empty (no policies uploaded yet), the engine returns a graceful fallback message — no crash, no hallucination.

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key with access to `gpt-4o-mini` and `text-embedding-3-small`

### 1. Clone the repository

```bash
git clone <repo-url>
cd aarogyaaid
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Edit .env and fill in OPENAI_API_KEY, JWT_SECRET, ADMIN_USERNAME, ADMIN_PASSWORD
```

### 3. Frontend setup

```bash
cd ../frontend
npm install
```

---

## Environment Variables

All variables are defined in `backend/.env`. Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | SQLite path (`sqlite:///./aarogyaaid.db`) or PostgreSQL URL |
| `OPENAI_API_KEY` | Yes | Your OpenAI API key — used for GPT-4o-mini and embeddings |
| `JWT_SECRET` | Yes | Long random string for signing JWT tokens. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_USERNAME` | Yes | Username for the admin account (not stored in DB) |
| `ADMIN_PASSWORD` | Yes | Password for the admin account (not stored in DB) |
| `CHROMA_PATH` | No | Path to ChromaDB storage directory. Defaults to `./chroma_db` |

---

## Running the Application

### Start the backend

```bash
cd backend
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### Start the frontend

```bash
cd frontend
npm run dev
```

App available at: http://localhost:5173

### First-time setup after starting

1. Log in at http://localhost:5173 using your `ADMIN_USERNAME` and `ADMIN_PASSWORD`
2. Go to the Admin dashboard
3. Upload the three sample policy documents from `sample-data/`
4. Log out, create a regular user account, and test the recommendation flow

---

## Testing

Tests are located in `backend/tests/`. They mock all external dependencies (OpenAI, ChromaDB) and run fully offline.

```bash
cd backend
venv\Scripts\activate

# Run all tests with verbose output
pytest tests/ -v

# Run a specific test class
pytest tests/test_recommendation.py::TestGenerateRecommendation -v

# Run with coverage report
pytest tests/ -v --tb=short
```

**21 tests** covering:
- Query generation logic (5 tests)
- Recommendation engine with mocked OpenAI + ChromaDB (7 tests)
- Chunk service (5 tests)
- Security utilities — password hashing and JWT (4 tests)

---

## Project Structure

```
aarogyaaid/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── chat_engine.py        # Chat RAG + OpenAI call
│   │   │   ├── prompts.py            # System prompts
│   │   │   └── recommend_engine.py   # Recommendation RAG + OpenAI call
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic settings from .env
│   │   │   ├── database.py           # SQLAlchemy engine + session
│   │   │   └── security.py           # bcrypt + JWT utilities
│   │   ├── models/
│   │   │   ├── user.py               # User SQLAlchemy model
│   │   │   └── policy.py             # Policy SQLAlchemy model
│   │   ├── routes/
│   │   │   ├── auth.py               # Login, get_current_user, require_admin
│   │   │   ├── recommend.py          # POST /api/recommend
│   │   │   ├── chat.py               # POST /api/chat
│   │   │   └── admin.py              # Upload, list, edit, delete policies
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── chunk_service.py      # Sliding window text chunker
│   │   │   ├── file_service.py       # File save/delete utilities
│   │   │   ├── parser_service.py     # PDF / TXT / JSON text extraction
│   │   │   └── vector_service.py     # ChromaDB + OpenAI embeddings
│   │   └── main.py                   # FastAPI app, CORS, router registration
│   ├── tests/
│   │   └── test_recommendation.py    # 21 pytest tests
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatPanel.jsx         # Sticky chat panel with RAG-backed replies
│       │   ├── PolicyTable.jsx       # Admin policy table with inline edit/delete
│       │   └── UploadCard.jsx        # Drag-and-drop policy upload form
│       ├── context/
│       │   └── SessionContext.jsx    # Auth token + session state (localStorage)
│       ├── pages/
│       │   ├── LandingPage.jsx
│       │   ├── LoginPage.jsx
│       │   ├── SignupPage.jsx
│       │   ├── ProfilePage.jsx       # 6-field recommendation form
│       │   ├── ResultsPage.jsx       # Recommendation cards + chat panel
│       │   └── AdminPage.jsx         # Admin dashboard
│       ├── styles/                   # Plain CSS with design token variables
│       └── api/client.js             # Fetch wrapper with Bearer token injection
├── sample-data/
│   ├── careshield_basic.txt
│   ├── medprotect_plus.txt
│   └── activecover_premier.txt
├── README.md
├── PRD.md
└── demo-script.md
```

---

## Future Improvements

- **PostgreSQL in production** — swap `DATABASE_URL` to a managed Postgres instance; SQLAlchemy requires no code changes
- **Streaming chat responses** — use OpenAI's streaming API to show tokens as they arrive, reducing perceived latency
- **Multi-language support** — the system prompt can be extended to respond in Hindi, Tamil, or Bengali based on user preference
- **Policy comparison view** — a dedicated side-by-side table comparing two or three policies across all dimensions
- **Government scheme integration** — scrape and index Ayushman Bharat, PMJAY, and state scheme PDFs automatically
- **User history** — store past recommendations per user so they can revisit previous results
- **Feedback loop** — thumbs up/down on recommendations feeds a fine-tuning or re-ranking layer
- **Rate limiting** — add per-user API rate limits to control OpenAI spend in production
- **Docker Compose** — containerise backend + ChromaDB for one-command deployment
