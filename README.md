# The Engineering Commons — Backend

FastAPI service backing the [Blog](../Blog) frontend. Provides content, auth
(email/password + OAuth federation), and interactions (likes, bookmarks, drafts).

## Stack
- **FastAPI** + **SQLModel** (SQLAlchemy 2.0) + **Pydantic v2**
- **SQLite** locally (`blog.db`); swap `DATABASE_URL` for a managed Postgres later
- **bcrypt** password hashing + **JWT** (PyJWT) bearer tokens
- Managed with **uv** (Python 3.12)

## Run

```bash
cd BlogBackend
cp .env.example .env          # then edit JWT_SECRET
uv run uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000   ·   Interactive docs: http://localhost:8000/docs
- On first start it creates `blog.db` and seeds the demo dataset (disciplines,
  authors, articles). Delete `blog.db` to reset.

The frontend talks to it via `NEXT_PUBLIC_API_URL=http://localhost:8000` (set in
`Blog/.env.local`). CORS allows `http://localhost:3000`.

## API surface

Responses are **camelCase** to match the frontend TypeScript types exactly.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/articles?discipline=&q=` | — | Feed (published), filter + search |
| GET | `/articles/{slug}` | optional | Article (+ viewer like/bookmark state); drafts → owner only |
| GET | `/articles/{slug}/related` | optional | Related articles |
| GET | `/disciplines` | — | Disciplines |
| GET | `/topics/trending` | — | Top tags |
| GET | `/contributors/top` | — | Top authors |
| GET | `/authors/{handle}` | — | Author profile |
| GET | `/authors/{handle}/articles` | optional | Author's published articles |
| POST | `/auth/register` | — | Create account → `{user, accessToken}` |
| POST | `/auth/login` | — | Email/password → `{user, accessToken}` (401 on bad creds) |
| POST | `/auth/oauth` | — | Federate a NextAuth OAuth sign-in → `{user, accessToken}` |
| GET | `/auth/me` | Bearer | Current user |
| POST | `/articles` | Bearer | Create article/draft → `{slug, title, status}` |
| GET | `/me/drafts` | Bearer | The user's drafts |
| GET | `/me/bookmarks` | Bearer | The user's bookmarks |
| POST/DELETE | `/articles/{slug}/like` | Bearer | Like / unlike |
| POST/DELETE | `/articles/{slug}/bookmark` | Bearer | Bookmark / unbookmark |

## Layout

```
app/
  main.py          FastAPI app, CORS, startup seed
  config.py        settings (.env)
  database.py      engine + session
  models.py        SQLModel tables
  schemas.py       Pydantic request/response (camelCase)
  security.py      bcrypt + JWT + current-user deps
  serializers.py   ORM → schema
  seed.py          demo dataset
  routers/         content.py · auth.py · interactions.py
```

## Notes
- Each registered (or OAuth-federated) user gets an **Author** profile with a
  unique `handle`; the frontend maps the session to `/authors/{handle}`.
- Article bodies arrive as rich HTML from the TipTap editor and are **sanitized**
  with `nh3` on write (safe tag/attr allowlist) — the client renders them as HTML,
  so scripts/handlers are stripped server-side. Excerpt + reading time are derived
  from the stripped text.
- `blog.db`, `.env`, and `.venv` are gitignored.
