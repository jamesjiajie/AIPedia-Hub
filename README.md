# AIpedia Hub

Personal, local-first knowledge base for AI tools.

## Development

Start the API:

```bash
cd backend
uv sync --all-groups
uv run uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:5173`. The API health check is available at
`http://localhost:8000/api/health`.

## Agnes smart drafts

Copy `backend/.env.example` to `backend/.env`, then set `AGNES_API_KEY`. The key is
read only by the API server; do not add it to the frontend or commit the `.env` file.
Open `/discover` to paste trusted source excerpts and generate a reviewable tool-card
draft with `agnes-2.5-flash`. The model never fetches arbitrary URLs and the card is
saved only after you review it.

## Checks

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && pnpm lint && pnpm build
```

## Data

The default SQLite database is `backend/aipedia.db`. Back it up only after
stopping the application or by using SQLite's online backup mechanism.
