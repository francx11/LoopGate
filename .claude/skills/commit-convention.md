# Skill: Commit Convention

## Rules (always apply — no exceptions)

1. **English only** — subject line and body, regardless of the language used in conversation.
2. **Conventional Commits** format: `<type>(<optional scope>): <subject>`
   - Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`, `perf`
   - Subject: imperative mood, no period at end ("add X", not "added X" or "adds X.")
3. **No co-authorship trailer** — never append `Co-Authored-By:` lines.

## Format

```
<type>(<scope>): <short subject>

<optional body — wrap at 72 chars>
```

## Examples

```
feat(tasks): add working directory field to task model
```
```
fix(ws): use saved event loop reference in broadcast_sync
```
```
refactor(executor): extract env builder to separate function
```
```
chore: update .gitignore to exclude dist artifacts
```

## What NOT to do

```
# Wrong — Spanish
fix(ws): arreglar broadcast_sync que usaba el loop incorrecto

# Wrong — co-authorship trailer
feat: add heartbeat

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

# Wrong — past tense
fix: fixed the reconnect timer cleanup

# Wrong — no type prefix
update WebSocket reconnect logic
```
