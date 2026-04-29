# 01 Setup

> Environment setup, dependencies, ports, and quick commands for the multi-app sample stack.

## Prerequisites

| Requirement | Version | Notes                                        |
| ----------- | ------- | -------------------------------------------- |
| Node.js     | ≥20     | Required for React clients; use `nvm use 20` |
| Python      | 3.9+    | Required for backend                         |
| npm         | ≥9      | Package manager for React clients            |
| pip         | latest  | Python dependency management                 |

- React clients use **npm** (not pnpm/yarn); always use `--legacy-peer-deps`
- `package-lock.json` is gitignored in both React clients
- Pre-commit hook runs Prettier on markdown — run `npx prettier --write` before committing `.md` files
- Commit-msg hook blocks "claude" (case-insensitive) — omit AI tool names

## Ports

| App                       | Port | Profile |
| ------------------------- | ---- | ------- |
| simple-backend            | 8082 | —       |
| react-voice-client        | 8083 | VOICE   |
| react-video-client-avatar | 8084 | VIDEO   |

## Quick Start

### Backend

```bash
cd simple-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-local.txt
cp .env.example .env  # edit with your Agora credentials
python3 -u local_server.py
```

### Voice Client

```bash
cd react-voice-client
npm install --legacy-peer-deps
npm run dev
```

### Video Avatar Client

```bash
cd react-video-client-avatar
npm install --legacy-peer-deps
npm run dev
```

## Required Environment Variables (Backend)

| Variable          | Purpose                    | Required? |
| ----------------- | -------------------------- | --------- |
| `APP_ID`          | Agora App ID               | Yes       |
| `APP_CERTIFICATE` | Agora App Certificate      | Yes       |
| `CUSTOMER_ID`     | Agora REST API customer ID | Yes       |
| `CUSTOMER_SECRET` | Agora REST API secret      | Yes       |

Profile-specific variables use the pattern `<PROFILE>_<VARIABLE>` (e.g., `VOICE_TTS_VENDOR=rime`).

## Quick Commands

| Command                      | Where          | What It Does               |
| ---------------------------- | -------------- | -------------------------- |
| `python3 -u local_server.py` | simple-backend | Start backend (unbuffered) |
| `npm run dev`                | react clients  | Start Next.js dev server   |
| `npm run build`              | react clients  | Production build           |
| `pytest`                     | simple-backend | Run backend tests          |
| `npx prettier --write .`     | any directory  | Format markdown files      |

## PM2 Production Mode

```bash
pm2 start ecosystem.config.js
```

Starts all apps (backend + both clients) with correct ports and environment variables.

## Common Setup Issues

- **Python output buffering** — always use `python3 -u` or `PYTHONUNBUFFERED=1`; without this, logs silently buffer
- **npm vs pnpm** — this repo uses npm, not pnpm; `pnpm install` will not work
- **Node version** — Next.js 16 requires Node ≥20.9.0; use `nvm use 20`
- **Missing --legacy-peer-deps** — React 19 + some packages need `--legacy-peer-deps`
- **MLLM_LOCATION not MLLM_REGION** — Agora expects `MLLM_LOCATION` (e.g., `us-central1`)

## Related Deep Dives

- [Profile Configuration](L2/profile_configuration.md) — Profile-based env var system, MLLM setup, vendor config
