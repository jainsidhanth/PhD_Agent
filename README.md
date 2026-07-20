# PhD Outreach Agent

An AI-powered personal tool that **discovers, scores, and manages cold outreach to PhD
supervisors**. It replaces a spreadsheet and hours of manual CV tailoring: find relevant
professors per research track, score them on four dimensions, generate a tailored CV / SOP /
research proposal / outreach email, and track the full outreach lifecycle.

Powered by **Claude (Anthropic API)**. Fully self-hostable — no third-party platform required.

## Stack
- **Frontend:** React 19 (Tailwind, Phosphor icons, Framer Motion)
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **AI:** Anthropic Claude (`claude-sonnet-4-6` by default)
- **Docs:** python-docx (Markdown → .docx export)

## Features
- **Discover** — "Find Professors" per research track (1–5 each) with a ranked table and 5
  progress-bar score columns (research fit, methods overlap, lab activity, program strength, overall).
  University rank is editable inline and recomputes the program-strength score.
- **Outreach** — collapsible cards: Generate Brief → Generate Package (CV / SOP / proposal / email)
  → download the three `.docx` files → copy the email → Mark as Sent / Skip.
- **History** — response / interested toggles, notes, and a manual-entry form for professors
  contacted outside the app.
- **Profile** — edit the ground-truth base CV, research proposal, and sample email used for generation.

---

## Prerequisites
- An **Anthropic API key** — get one at https://console.anthropic.com/ (Settings → API Keys).
  Billing must be enabled.
- Either **Docker** (easiest) **or** Node 20 + Python 3.11 + MongoDB installed locally.

---

## Option A — Run with Docker (recommended)

```bash
# 1. Clone
git clone https://github.com/<you>/phd-outreach-agent.git
cd phd-outreach-agent

# 2. Provide your Claude key (used by docker-compose)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Build & run everything (frontend + backend + mongo)
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- MongoDB: localhost:27017 (data persisted in a named volume)

To stop: `docker compose down` (add `-v` to also wipe the database).

---

## Option B — Run locally without Docker

### 1. MongoDB
Install and start MongoDB locally, or use a free **MongoDB Atlas** cluster and copy its
connection string.

### 2. Backend
```bash
cd backend
cp .env.example .env          # then edit .env and set ANTHROPIC_API_KEY + MONGO_URL
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend
```bash
cd frontend
cp .env.example .env          # REACT_APP_BACKEND_URL=http://localhost:8001
yarn install
yarn start                    # opens http://localhost:3000
```

---

## Environment variables

### `backend/.env`
| Variable            | Description                                          |
|---------------------|------------------------------------------------------|
| `MONGO_URL`         | MongoDB connection string                            |
| `DB_NAME`           | Database name (e.g. `phd_outreach`)                  |
| `CORS_ORIGINS`      | Allowed origins, comma-separated (`*` for all)       |
| `ANTHROPIC_API_KEY` | Your Claude API key (`sk-ant-...`)                   |
| `CLAUDE_MODEL`      | Optional model override (default `claude-sonnet-4-6`)|

### `frontend/.env`
| Variable                  | Description                                    |
|---------------------------|------------------------------------------------|
| `REACT_APP_BACKEND_URL`   | URL of the backend as reachable by the browser |

> All backend routes are served under the `/api` prefix.

---

## Deploying to production
- **Backend** → any container host (Railway, Render, Fly.io, a VPS). Set the env vars above.
- **Frontend** → build (`yarn build`) and serve the static `build/` folder (Vercel, Netlify, Nginx).
  Set `REACT_APP_BACKEND_URL` to your public backend URL **before** building.
- **Database** → MongoDB Atlas free tier works well; point `MONGO_URL` at it.

## Cost notes
Uses your own Anthropic billing. Rough guide: research brief ~$0.01, a full package
(CV + SOP + proposal + email) ~$0.05-0.15 per professor. Generate the brief first to filter
out poor fits before committing to a package.

## Security
- Never commit real secrets. `.env` files are gitignored; only `.env.example` templates are tracked.
- Rotate your Anthropic key if it is ever exposed.

## Project layout
```
backend/     FastAPI app (server.py), scoring (domain.py), Claude calls (llm_service.py), docx (docgen.py)
frontend/    React app (src/pages: Discover, Outreach, History, Profile)
docker-compose.yml
```

## License
Personal project — use freely.
