# 04 Conventions

> Coding patterns, naming rules, error handling, and testing standards used across the sample stack.

## Language-Specific Conventions

### Python (Backend)

- **Module organization** — business logic in `core/`, Flask routes in `local_server.py`
- **Configuration** — centralized in `core/config.py`, lazy-loaded via `initialize_constants(profile)`
- **Docstrings** — present for public functions and classes
- **Error handling** — `ValueError` for config validation, `jsonify()` for HTTP responses
- **Secrets** — always redacted in debug output (regex on sensitive key names)
- **Unbuffered output** — always `python3 -u` or `PYTHONUNBUFFERED=1`

### TypeScript/React (Clients)

- **File naming** — PascalCase for components (`VoiceClient.tsx`), camelCase for hooks (`useAgoraVoiceClient.ts`)
- **Hooks** — `use*` prefix, return types explicitly typed
- **State management** — React hooks only (no Redux, no external state library)
- **useState/useRef** — always typed (e.g., `useState<string | null>(null)`)
- **useEffect** — dependencies always specified (no infinite loops)

## API Naming

| Context          | Convention        | Example                         |
| ---------------- | ----------------- | ------------------------------- |
| Query parameters | lowercase + `_`   | `channel`, `pipeline_id`        |
| JSON payload     | camelCase         | `enable_rtm`, `system_messages` |
| Env variables    | UPPER_SNAKE_CASE  | `VOICE_TTS_VENDOR`              |
| Profile prefix   | `<PROFILE>_<VAR>` | `VIDEO_AVATAR_VENDOR`           |

## Profile System

- Profile names are case-insensitive (VOICE, voice, Voice all work)
- Pattern: `<PROFILE>_<VARIABLE>` — single underscore between profile and variable name
- No fallback: if `VOICE_APP_ID` is empty, it does **not** fall back to `APP_ID`
- Profiles loaded lazily at request time, not at startup

## Git Hooks

- **Pre-commit** — runs Prettier on markdown files; always run `npx prettier --write` before committing `.md`
- **Commit-msg** — blocks messages containing "claude" (case-insensitive)
- **No Co-Authored-By** — omit AI attribution lines

## Commit Messages

- Lowercase start, present tense
- No AI tool names (claude, cursor, copilot, etc.)
- Format: `type: description` — e.g., `feat: add mcp server config`

## Package Management

- **React clients** — npm only, always `--legacy-peer-deps`
- `package-lock.json` is gitignored in both React clients
- **Backend** — pip with `requirements-local.txt` for local dev

## Testing

- **Backend** — pytest framework with fixtures in `simple-backend/tests/`
- **Clients** — manual testing + UI kit storybook; no unit test files in client directories
- Coverage thresholds not enforced (sample code, not production library)

## Secret Handling in Debug Output

- Backend redacts secrets in `/start-agent?debug=1` responses
- Regex pattern: `(key|token|api_key|secret|certificate|password|authorization|credentials)`
- Strings >8 chars matching: `XXXX***XXXX`
- Curl debug dumps saved to `/tmp/agora_curl_*_YYYYMMDD_HHMMSS.sh`

## CORS Pattern

- If request includes `Authorization` header: response uses specific `Origin` + `Credentials: true`
- Otherwise: `Access-Control-Allow-Origin: *`
- Preflight (`OPTIONS`) handled for all routes

## URL Parameter Conventions

- React clients read URL params for automation: `?profile=voice&autoconnect=true&returnurl=...`
- Profile param overrides the default profile for backend calls
- `autoconnect=true` starts the agent immediately on page load (used in OAuth return flow)

## Related Deep Dives

- [Profile Configuration](deep_dives/profile_configuration.md) — Full profile system details
