# AarogyaAid — Demo Script

**Target duration:** 3–4 minutes  
**Audience:** Reviewers / evaluators  
**Setup required:** Both servers running, three sample policies already uploaded

---

## Pre-demo checklist

- [ ] Backend running: `uvicorn app.main:app --reload` on port 8000
- [ ] Frontend running: `npm run dev` on port 5173
- [ ] Three sample policies uploaded via Admin dashboard:
  - `careshield_basic.txt`
  - `medprotect_plus.txt`
  - `activecover_premier.txt`
- [ ] Browser open at http://localhost:5173
- [ ] Browser zoom at 100%, window maximised

---

## Scene 1 — Landing page (15 seconds)

**What to show:** Navigate to http://localhost:5173

**Speaking notes:**
> "AarogyaAid is an AI-powered health insurance advisor. The landing page explains the product in plain language — no jargon, no AI buzzwords. From here a user can sign in or create an account."

**Click:** "Get started" button

---

## Scene 2 — Sign up and login (30 seconds)

**What to show:** The signup page

**Speaking notes:**
> "New users register with a username and password. The backend auto-creates the account on first login — no separate registration endpoint needed."

**Action:** Enter username `priya_demo` and a password, click "Create account"

> "The user is immediately taken to their profile form. The JWT token is stored in localStorage and attached to every subsequent API request."

---

## Scene 3 — Profile form (45 seconds)

**What to show:** The profile form at `/profile`

**Speaking notes:**
> "The form collects exactly six fields that drive the recommendation engine. Each field has a specific influence on the retrieval query."

**Fill in:**
- Full name: `Priya Sharma`
- Age: `34`
- City: `Metro city`
- Lifestyle: `Sedentary`
- Pre-existing conditions: check `Diabetes`
- Income: `₹3–8 lakh`

> "Notice the checkbox cards — each condition is a first-class input, not a free-text field. This ensures the retrieval query is precise."

**Click:** "Find my plan →"

> "The backend converts this profile into a semantic search query, retrieves the top-10 most relevant chunks from ChromaDB, and sends them to GPT-4o-mini along with a strict JSON output schema."

---

## Scene 4 — Results page (60 seconds)

**What to show:** The results page at `/results`

**Speaking notes:**
> "The results page has two panels. On the left: the recommendation. On the right: the chat panel."

**Point to the best-fit card:**
> "MedProtect Plus is recommended because it has the shortest pre-existing disease waiting period for diabetes — two years versus four years for CareShield Basic. The engine found this by reading the actual uploaded policy documents, not from a training dataset."

**Point to the Why section:**
> "The explanation mentions Priya by name, references her city tier, income band, and diabetes condition — all three profile fields the system prompt requires."

**Point to the citations:**
> "Every factual claim cites the source document and page number. This is the anti-hallucination guarantee."

**Point to the peer comparison:**
> "The other plans are shown with suitability scores so the user can make an informed comparison."

---

## Scene 5 — Chat panel (45 seconds)

**What to show:** The chat panel on the right side of the results page

**Speaking notes:**
> "The chat panel opens with a personalised greeting. It already knows Priya's name and the recommended policy."

**Type and send:** `What is the waiting period for my diabetes?`

> "The chat engine performs a second RAG retrieval, this time filtered to the recommended policy only. The answer cites the specific page of the MedProtect Plus document."

**Type and send:** `Is there a co-pay for metro hospitals?`

> "The assistant answers from the document — 10% co-pay for claims above ₹50,000 in metro cities. It defines co-pay in plain language because the system prompt instructs it to define jargon on first use."

> "Chat history persists in localStorage, so if the user refreshes the page, the conversation is still there."

---

## Scene 6 — Admin dashboard (45 seconds)

**What to show:** Log out, log back in as admin

**Speaking notes:**
> "The admin dashboard is role-protected. A regular user token cannot access it — the backend returns 403."

**Log in as admin** (use ADMIN_USERNAME / ADMIN_PASSWORD from .env)

> "The admin sees all uploaded policies in a table with file type badges, upload dates, and status."

**Show the upload card:**
> "Uploading a new policy triggers the full RAG pipeline: parse → chunk → embed → store in ChromaDB. If the pipeline fails, the database record is rolled back — no orphaned metadata."

**Click Edit on a policy:**
> "Inline editing — the row becomes editable without a modal or page navigation. Save calls PATCH, cancel discards changes."

**Click Delete on a policy:**
> "Delete shows an inline confirmation row before calling the API. The backend deletes the file, removes the ChromaDB vectors, and drops the SQL record in one transaction."

---

## Scene 7 — Tests (15 seconds, optional)

**What to show:** Terminal

```bash
cd backend
pytest tests/ -v
```

**Speaking notes:**
> "21 tests covering the recommendation engine, chunking service, and security utilities. All external dependencies are mocked — tests run offline without an API key."

---

## Key talking points for Q&A

- **Why not Google ADK?** — ADK is an agent orchestration framework suited for multi-step tool-calling. This product uses a two-step RAG pattern (retrieve → generate) where direct SDK calls give more control over retrieval filtering, output schema enforcement, and latency.
- **How is hallucination prevented?** — The system prompt explicitly forbids stating facts not present in the retrieved documents. The `response_format={"type": "json_object"}` parameter enforces structured output at the API level.
- **What happens with no policies uploaded?** — The engine returns a graceful fallback message. No crash, no hallucination.
- **How does the admin-only route work?** — `require_admin` is a FastAPI dependency that decodes the JWT and checks `role == "admin"`. The admin account is validated against environment variables, not the database.

---

## Screenshots to include (if no video)

1. Landing page — full viewport
2. Profile form — filled in with the demo profile
3. Results page — best-fit card visible, chat panel visible
4. Chat panel — showing a question and a cited answer
5. Admin dashboard — policy table with all three sample policies
6. Admin dashboard — inline edit row active
7. Terminal — `pytest tests/ -v` output showing 21 passed

---

## Recording tips

- Use OBS Studio or Loom (free tier)
- Record at 1920×1080, 30fps
- Disable browser notifications before recording
- Use a clean browser profile with no extensions visible
- Narrate while clicking — silence is awkward in demo videos
- Keep the cursor moving slowly and deliberately
- Trim the start and end — reviewers notice dead time
