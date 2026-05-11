# Contributing to Loopgate

## Setup

```bash
git clone https://github.com/francx11/loopgate.git
cd loopgate

# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # edit SECRET_TOKEN

# Frontend
cd ../frontend
npm install
```

## Running locally

```bash
# Backend (terminal 1)
cd backend && python run.py

# Frontend dev server (terminal 2)
cd frontend && npm run dev
# → http://localhost:5173 (proxies API to :8000)
```

Or run both at once with `start.bat` (Windows) / `scripts/start.sh` (Linux/macOS).

## Running tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend build check
cd frontend && npm run build

# Lint
cd backend && ruff check app/ tests/
cd frontend && npm run lint
```

## Commit convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): add thing
fix(scope): correct behavior
refactor(scope): restructure without behavior change
test(scope): add / update tests
docs(scope): documentation only
chore(scope): tooling, CI, config
```

- **Language**: English only
- **No** `Co-Authored-By:` trailers
- One logical unit per commit

## Pull requests

1. Open an issue first for non-trivial changes.
2. Branch from `main`: `feature/<name>` or `fix/<name>`.
3. CI must be green before merging.
4. For security changes: ping a reviewer with the `/security-review` skill.

## Security

See [SECURITY.md](SECURITY.md) for the threat model and how to report vulnerabilities.

## Code conventions

See [CLAUDE.md](CLAUDE.md) — these conventions apply to human contributors too.
