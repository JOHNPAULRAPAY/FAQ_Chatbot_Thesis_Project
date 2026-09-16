# Student Assistant Chatbot

A hybrid rule-based + machine learning chatbot that answers common questions from students and incoming enrollees — admissions, tuition, enrollment, and document requests — with support for program-specific and admission-level-specific answers.

Built as a thesis project, this chatbot is designed to be reliable without an internet-connected AI service, while remaining architecturally ready to plug in a real LLM later if needed.

---

## Features

- **Hybrid intent recognition** — combines deterministic rule matching with a trained ML classifier (TF-IDF + Logistic Regression), using confidence thresholds to decide which to trust
- **Entity extraction** — recognizes college programs (e.g. "BSCS" → Computer Science) and SHS strands (e.g. "STEM") using spaCy's `PhraseMatcher`
- **Context-aware conversations** — remembers what it's waiting to hear (e.g. "which level are you asking about?") across multiple messages, and auto-infers admission level from a mentioned program/strand
- **Safety-first design** — critical intents (like ending a conversation) are always handled by deterministic rules, never left to ML or an LLM
- **Optional LLM fallback layer** — stubbed and disabled by default; the system works fully without it, and it activates only when rules + ML both fail to understand a message
- **Persistent conversation history** — stored in SQLite via SQLAlchemy (users, conversations, messages, feedback)
- **REST API** — built with FastAPI, with CORS, rate limiting, input validation, and centralized error handling
- **Web chat interface** — plain HTML/CSS/JS frontend, no framework dependencies
- **Automated test suite** — 16 tests covering rule matching, ML classification, the API, and edge cases

---

## Architecture

```
User (browser)
    │
    ▼
Frontend (docs/index.html)
    │  HTTP POST /chat
    ▼
FastAPI backend (app/api.py)
    │
    ├─→ ConversationState (per-session memory)
    │
    ├─→ Hybrid Engine (app/chatbot/engine.py)
    │       │
    │       ├─→ Rule matching (word-overlap on intents.json patterns)
    │       │     — always wins for RULE_ONLY_INTENTS (e.g. goodbye)
    │       │
    │       ├─→ ML Classifier (app/ml/classifier.py)
    │       │     — TF-IDF + Logistic Regression
    │       │     — used when confidence ≥ 0.5
    │       │
    │       ├─→ Entity Extraction (app/chatbot/entities.py)
    │       │     — spaCy PhraseMatcher: programs, SHS strands, admission level
    │       │
    │       └─→ LLM Layer (app/chatbot/llm_layer.py) — STUBBED
    │             — only activates if rules + ML both fail
    │             — disabled by default (no API key configured)
    │
    └─→ Database (app/database/models.py) — SQLite via SQLAlchemy
```

**Design principle:** every layer is replaceable without breaking the others. The CLI and the API both call the same `get_response()` function; rules and ML share `intents.json` as a single source of truth; the LLM layer is fully optional and the chatbot is provably functional without it.

---

## Project Structure

```
FAQ_Chatbot/
├── app/
│   ├── main.py                  # CLI entry point
│   ├── api.py                   # FastAPI entry point
│   ├── chatbot/
│   │   ├── engine.py            # hybrid rules+ML decision logic
│   │   ├── preprocessing.py     # normalization + lemmatization
│   │   ├── conversation.py      # per-session state
│   │   ├── entities.py          # program/strand/level extraction
│   │   └── llm_layer.py         # stubbed LLM fallback
│   ├── database/
│   │   └── models.py            # SQLAlchemy models
│   ├── ml/
│   │   ├── classifier.py        # training + prediction
│   │   └── model.pkl            # trained model (gitignored, regenerate via training)
│   └── data/
│       └── intents.json         # single source of truth: patterns + responses
├── docs/                        # frontend (named for GitHub Pages compatibility)
│   └── index.html
├── tests/
│   ├── test_rule_engine.py
│   ├── test_ml_classifier.py
│   ├── test_api.py
│   └── test_edge_cases.py
├── .env                         # local config (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### Requirements
- Python 3.11 or 3.12 recommended (project has also been run on 3.14)

### 1. Clone and create a virtual environment

```powershell
git clone <your-repo-url>
cd FAQ_Chatbot
python -m venv venv
venv\Scripts\Activate.ps1
```

> If PowerShell blocks the activation script, run this once:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Train the ML model

```powershell
python -m app.ml.classifier
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
DATABASE_URL=sqlite:///chatbot.db
ALLOWED_ORIGINS=*
ANTHROPIC_API_KEY=
```

---

## Running Locally

**CLI version:**
```powershell
python -m app.main
```

**API + Web UI:**
```powershell
python -m uvicorn app.api:app --reload
```
Then open `docs/index.html` in a browser. Interactive API docs are available at `http://127.0.0.1:8000/docs`.

---

## Testing

```powershell
python -m pytest tests/ -v
```

Covers: rule-based matching, text normalization/lemmatization, ML classifier sanity checks, API request/response validation, conversation persistence, fallback/escalation behavior, and critical-intent safety (e.g. "goodbye" always exits regardless of ML confidence).

---

## Maintenance

### Adding a new intent

1. Add an entry to `app/data/intents.json` with a `tag`, several example `patterns`, and `responses`
2. Retrain the model: `python -m app.ml.classifier`
3. If the intent is safety-critical, add its tag to `RULE_ONLY_INTENTS` in `app/chatbot/engine.py`
4. Test via CLI or `/docs` before deploying

### Adding a new entity category (e.g. campus, semester)

Add a new key to `ENTITY_DEFINITIONS` in `app/chatbot/entities.py`, following the existing `{canonical_name: [aliases]}` shape — no other code changes needed to detect it.

### Retraining the ML model

Required whenever `intents.json` patterns change (not required for response-text-only changes):
```powershell
python -m app.ml.classifier
```
This regenerates `app/ml/model.pkl`, which is gitignored and rebuilt automatically during deployment.

---

## Deployment

- **Backend**: deployed on [Render](https://render.com) (free tier)
  - Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm && python -m app.ml.classifier`
  - Start command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
- **Frontend**: deployed on GitHub Pages, served from the `docs/` folder
- `ALLOWED_ORIGINS` is set on the backend to the exact frontend origin (no wildcard) in production

**Known limitation:** SQLite on Render's free tier is not guaranteed to persist across redeploys, since the filesystem is ephemeral. Acceptable for a thesis demo; a hosted Postgres database is a natural upgrade path.

---

## Future Improvements

- Store per-program tuition/requirement data for fully customized answers (beyond the current `[Regarding X]` tagging)
- Use remembered context (`ConversationState`) so follow-up questions don't require repeating the program/level
- Add fuzzy spelling correction for typos (e.g. "henlo") that lemmatization alone doesn't fix
- Activate the real LLM layer if budget/approval allows
- Migrate to a persistent hosted database for production
- Wire the existing `feedback` database table to UI buttons (thumbs up/down) to collect real response-quality data
- Build a simple admin view of common fallback questions to guide which new intents to add next

---

## Tech Stack

Python · FastAPI · SQLAlchemy · SQLite · scikit-learn · spaCy · pytest · HTML/CSS/JavaScript