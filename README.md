# AIPedia Hub 🚀

Welcome to **AIPedia Hub** — your central knowledge repository and curated directory for everyday Artificial Intelligence. 

Whether you are looking to discover practical AI tools, master prompt techniques, or stay updated on recent AI workflows, this project brings together actionable insights and resource guides in one place.

### ✨ Key Features
* 🧠 **AI Knowledge Base**: Clear explanations of core AI concepts, terminology, and practical guides.
* 🛠️ **Tool Directory**: A carefully selected list of AI tools for productivity, development, creativity, and automation.
* 💡 **Best Practices & Prompts**: Real-world use cases, prompt engineering tips, and workflow optimizations.

This implementation is a personal, local-first knowledge base for AI tools.

## Development

Start the API:

```bash
cd backend
uv sync --all-groups
uv run uvicorn app.main:app --reload --port 8001
```

In a second terminal, start the frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:5173`. The API health check is available at
`http://localhost:8001/api/health`.

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
