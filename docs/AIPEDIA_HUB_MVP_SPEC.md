# AIpedia Hub MVP Product and Technical Specification

> Status: Draft for implementation  
> Version: 0.1  
> Date: 2026-09-01  
> Primary language: Simplified Chinese  

## 1. Purpose

AIpedia Hub is a personal knowledge base for collecting and recalling AI tools.

The product must help the user answer three questions quickly:

1. What is this tool?
2. Why did I save it?
3. When should I use it?

The first release is a single-user web application. Its priority is fast capture,
reliable retrieval, and durable local ownership of data. It is not intended to be
a public AI-tool directory in the MVP.

## 2. Product principles

- **Memory before marketing:** `why_saved` and `use_cases` are more prominent than copied promotional text.
- **Capture in under 30 seconds:** a useful record can be created with only name, URL, and a memory note.
- **Search from anything remembered:** names, aliases, tags, summaries, use cases, and notes are searchable.
- **Archive instead of delete:** records should remain recoverable by default.
- **Local-first and portable:** the application must work with a single SQLite database file and support backup/export.
- **AI is optional enhancement:** basic capture and search must never depend on an AI service.

## 3. MVP scope

### 3.1 Included

- Create, view, edit, favorite, and archive a tool.
- Browse tools in card and compact-list views.
- Search across tool content in Chinese and English.
- Filter by category, tag, pricing model, favorite state, and record status.
- Sort by recently added, recently updated, last viewed, and name.
- Maintain categories and tags during tool editing.
- Detect duplicate canonical URLs before saving.
- Record created, updated, and last-viewed timestamps.
- Provide a clear empty state and a fast-add entry point.

### 3.2 Deferred

- Automatic URL metadata extraction and favicon download.
- AI-generated summaries, tags, or use cases.
- Semantic/vector search.
- Browser extension.
- User accounts, permissions, sharing, and collaboration.
- Public SEO pages.
- Native mobile or desktop application.

### 3.3 Explicit non-goals

- Do not scrape or mirror complete third-party websites.
- Do not require Elasticsearch, a vector database, Redis, or a task queue.
- Do not introduce authentication while the application is local-only.
- Do not permanently delete records through the normal MVP interface.

## 4. Primary user flows

### 4.1 Quick capture

1. User selects **Add tool** from any screen.
2. User enters a tool name and official URL.
3. User records why the tool was saved and when it may be useful.
4. User optionally adds summary, category, tags, pricing model, platform, source URL, and notes.
5. The system normalizes the URL and warns if a matching record already exists.
6. The new record is saved and its detail page is opened.

Required fields:

- `name`
- At least one of `official_url`, `why_saved`, or `summary`

### 4.2 Recall and search

1. User focuses the global search field on the library page.
2. Search updates after a short debounce.
3. Results rank exact name matches first, then aliases/tags, then descriptive content.
4. User can combine text search with filters.
5. Opening a result updates `last_viewed_at`.

### 4.3 Review and maintain

1. User opens a tool detail page.
2. The page emphasizes **Why I saved this** and **When to use it**.
3. User edits the record, marks it as a favorite, visits its official URL, or archives it.
4. Archived records disappear from the default library but remain searchable when the archived filter is enabled.

## 5. Information architecture

### 5.1 Routes

| Route | Purpose |
| --- | --- |
| `/` | Tool library, global search, filters, and sorting |
| `/tools/new` | Create a tool; may also be presented as a drawer/modal from `/` |
| `/tools/:id` | Tool detail |
| `/tools/:id/edit` | Edit a tool |

### 5.2 Library page

- Persistent global search near the top.
- Primary **Add tool** action.
- Filter controls for category, tags, pricing, favorite, and status.
- Result count and active-filter summary.
- Card/list view switch.
- Cards show name, one-line summary, why saved, category, tags, favorite state, and update date.
- Default sort is most recently updated.

### 5.3 Tool detail page

Display order:

1. Name, favorite state, status, and official-site action.
2. One-line summary.
3. Why I saved this.
4. When to use it.
5. Category, tags, pricing model, and platforms.
6. Personal notes and discovery source.
7. Created, updated, and last-viewed metadata.
8. Edit and archive actions.

### 5.4 Example capture: Archify

Do not infer the product description without a verified URL. Present prompts such as:

```text
Name: Archify
Official URL: ...
One-line summary: ...
Why I saved it: I noticed that it can ...
When to use it: Use it next time I need to ...
```

## 6. Recommended technology stack

### 6.1 Frontend

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia only for genuinely shared client state
- Native `fetch` behind a typed API-client module
- Vitest for unit tests
- Playwright for critical end-to-end flows
- ESLint and Prettier

Use a client-rendered SPA for the MVP. Nuxt is unnecessary until public,
indexable content or server-side rendering becomes a product requirement.

### 6.2 Backend

- Current stable Python supported by all selected dependencies
- FastAPI
- Pydantic for API schemas and validation
- SQLAlchemy 2.x for persistence
- Alembic for every database schema change
- pytest for service and API tests
- Ruff for linting and formatting
- uv for Python versions, environments, dependencies, and lockfile

Prefer synchronous SQLAlchemy sessions for the SQLite MVP. Async database access
adds complexity without a meaningful benefit for a single-user, file-backed app.

### 6.3 Database and search

- SQLite stored as a single application data file.
- Enable `PRAGMA foreign_keys = ON` for every connection.
- Enable WAL mode for safer read/write coexistence.
- Use SQLite FTS5 with the trigram tokenizer for mixed Chinese/English substring search.
- Manage the FTS virtual table and synchronization triggers through Alembic migrations.
- Keep database access behind repositories/services so PostgreSQL can replace SQLite later.

### 6.4 Deployment

- Development: Vite and FastAPI run as separate development servers.
- Production MVP: FastAPI serves the API and the built frontend assets.
- Run as one application process with one SQLite data file.
- Never commit the live database file, local uploads, secrets, or environment files.
- Document backup and restore before treating the application as the canonical library.

## 7. Data model

### 7.1 `tools`

| Column | Type | Rules |
| --- | --- | --- |
| `id` | integer | Primary key |
| `name` | text | Required, trimmed |
| `slug` | text | Unique, generated, stable after creation |
| `aliases` | JSON text | Array of alternative names; default `[]` |
| `official_url` | text | Nullable, normalized |
| `canonical_url` | text | Nullable, unique when present |
| `source_url` | text | Nullable; where the user discovered the tool |
| `summary` | text | Nullable; concise description |
| `why_saved` | text | Nullable; personal memory anchor |
| `use_cases` | text | Nullable; situations in which the tool is useful |
| `notes` | text | Nullable; free-form personal notes |
| `category_id` | integer | Nullable foreign key to `categories.id` |
| `pricing_model` | text | `unknown`, `free`, `freemium`, `paid`, or `open_source` |
| `platforms` | JSON text | Array; default `[]` |
| `is_favorite` | boolean | Default `false` |
| `status` | text | `active`, `archived`, or `unavailable` |
| `created_at` | datetime | UTC, set on insert |
| `updated_at` | datetime | UTC, set on every update |
| `last_viewed_at` | datetime | Nullable UTC timestamp |

Store datetimes in UTC and convert them for display in the frontend.

### 7.2 `categories`

| Column | Type | Rules |
| --- | --- | --- |
| `id` | integer | Primary key |
| `name` | text | Required; case-insensitive unique |
| `slug` | text | Unique |

### 7.3 `tags`

| Column | Type | Rules |
| --- | --- | --- |
| `id` | integer | Primary key |
| `name` | text | Required; case-insensitive unique |
| `slug` | text | Unique |

### 7.4 `tool_tags`

| Column | Type | Rules |
| --- | --- | --- |
| `tool_id` | integer | Foreign key to `tools.id`, cascade delete |
| `tag_id` | integer | Foreign key to `tags.id`, cascade delete |

Use `(tool_id, tag_id)` as the composite primary key.

### 7.5 Search index

Index these values in an FTS5 virtual table:

- Name
- Aliases
- Summary
- Why saved
- Use cases
- Notes
- Category name
- Tag names

Desired result priority:

```text
exact name > name prefix > alias/tag > summary/why_saved/use_cases > notes
```

The service layer may combine explicit exact-match boosts with FTS5 `bm25()`
ranking. Queries shorter than three Unicode characters must fall back to a safe
`LIKE` search because of trigram-tokenizer behavior.

## 8. API contract

All endpoints use JSON under `/api`.

### 8.1 Tools

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/tools` | Search, filter, sort, and paginate tools |
| `POST` | `/api/tools` | Create a tool |
| `GET` | `/api/tools/{id}` | Get a tool and update its last-viewed time |
| `PATCH` | `/api/tools/{id}` | Partially update a tool |
| `POST` | `/api/tools/{id}/archive` | Archive a tool |
| `POST` | `/api/tools/{id}/restore` | Restore an archived tool |

`GET /api/tools` query parameters:

```text
q
category
tag (repeatable)
pricing_model
is_favorite
status (default: active)
sort (updated_desc, created_desc, viewed_desc, name_asc)
page (default: 1)
page_size (default: 24, maximum: 100)
```

Response shape:

```json
{
  "items": [],
  "page": 1,
  "page_size": 24,
  "total": 0
}
```

### 8.2 Taxonomy

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/categories` | List categories with usage counts |
| `POST` | `/api/categories` | Create a category during editing |
| `GET` | `/api/tags` | Search/list tags with usage counts |
| `POST` | `/api/tags` | Create a tag during editing |

### 8.3 Health

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Confirm app and database readiness |

### 8.4 Deferred API

`POST /api/url-preview` belongs to V1.1. It may retrieve a page title,
description, canonical URL, and favicon, but fetched values must remain editable
and must not overwrite personal notes.

## 9. Validation and behavior rules

- Trim all human-entered text before persistence.
- Normalize URL scheme, host casing, trailing slash, common tracking parameters, and fragments before duplicate comparison.
- Warn on duplicate canonical URL and link to the existing record.
- Do not silently merge two records.
- A name is required.
- At least one of official URL, summary, or why-saved text is required.
- Category and tag uniqueness is case-insensitive.
- Archive changes status; it does not remove the row.
- The public API does not expose a permanent-delete endpoint in the MVP.
- Failures must preserve user-entered form content and display an actionable message.

## 10. Suggested repository structure

```text
AIPedia-Hub/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── types/
│   │   └── views/
│   ├── tests/
│   ├── package.json
│   └── pnpm-lock.yaml
├── data/
│   └── .gitkeep
├── docs/
│   └── AIPEDIA_HUB_MVP_SPEC.md
├── .env.example
├── .gitignore
└── README.md
```

## 11. Implementation phases

### Phase 1: Foundation

- Scaffold frontend and backend.
- Configure formatting, linting, tests, environment variables, and CORS for development.
- Configure SQLite connections, foreign keys, WAL, and Alembic.
- Add `/api/health` and application startup checks.

### Phase 2: Core data

- Implement models, migrations, repositories, validation, and URL normalization.
- Implement tool, category, and tag APIs.
- Add API tests for create, update, duplicate warning, archive, restore, and pagination.

### Phase 3: Core interface

- Build library, create/edit form, and detail page.
- Add loading, empty, success, validation, and failure states.
- Add responsive layouts and keyboard-friendly controls.

### Phase 4: Search and filters

- Add and synchronize the FTS5 trigram index.
- Implement ranking, short-query fallback, filters, sorting, and pagination.
- Preserve active search/filter state in the URL query string.

### Phase 5: Hardening

- Add end-to-end tests for capture, recall, edit, favorite, archive, and restore.
- Build the frontend and serve it through FastAPI.
- Document startup, backup, restore, and database migration procedures.

## 12. MVP acceptance criteria

- A new tool can be recorded in under 30 seconds using the minimum fields.
- Reloading or restarting the application does not lose saved data.
- Searching by exact name returns that tool first.
- Searching a phrase from `why_saved`, `use_cases`, or notes returns the relevant tool.
- Chinese and English substring searches work for queries of three or more characters.
- One- and two-character searches still return correct results through fallback search.
- Search can be combined with category, tag, favorite, pricing, and status filters.
- Duplicate canonical URLs produce a warning and do not silently create a second record.
- Archived tools are absent from the default view and recoverable through restore.
- Core flows work at desktop and mobile widths and are keyboard accessible.
- Backend unit/API tests, frontend unit tests, end-to-end smoke tests, linters, and production builds pass.
- A documented backup can be restored into a fresh installation successfully.

## 13. Future evolution

### V1.1

- URL metadata preview and favicon handling.
- JSON/CSV export and import.
- Recently viewed and never-reviewed collections.

### V2

- Optional AI summary and tag suggestions.
- AI suggestions must be reviewed before saving.
- Screenshot or logo asset management.

### V3

- Browser extension and share-to-AIpedia capture flow.
- Optional semantic search after conventional search limitations are demonstrated.

### V4

- Authentication and multi-user ownership.
- Public/shareable tool pages and SEO.
- PostgreSQL migration and separate frontend/backend deployment.

## 14. Code-generation guardrails

When generating implementation code from this specification:

1. Implement phases in order and keep each phase independently runnable.
2. Do not add deferred infrastructure without a current requirement.
3. Generate and review an Alembic migration for every schema change.
4. Keep API schemas separate from persistence models.
5. Keep database operations out of route handlers; use repository/service layers.
6. Preserve personal fields during any future automated enrichment.
7. Write tests with each behavior instead of postponing them to the end.
8. Use stable dependency versions available at implementation time and commit both lockfiles.
9. Do not fabricate Archify or any other tool metadata without a verified source.
10. Treat this document as the MVP scope authority; record deliberate deviations before implementation.

