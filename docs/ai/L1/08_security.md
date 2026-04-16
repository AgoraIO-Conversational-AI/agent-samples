# 08 Security

> Security model, trust boundaries, credential handling, and auth options across the sample stack.

## Trust Boundaries

```
┌────────────────────────────────────┐
│  User's Browser (untrusted)        │
│  - No credentials stored           │
│  - Auth tokens in memory only      │
│  - Receives pre-generated tokens   │
└──────────────┬─────────────────────┘
               │ HTTP (CORS-protected)
┌──────────────▼─────────────────────┐
│  simple-backend (trusted)          │
│  - Holds all Agora credentials     │
│  - Generates v007 tokens           │
│  - Redacts secrets in debug output │
│  - Optional OAuth + SMS 2FA        │
└──────────────┬─────────────────────┘
               │ HTTP (authenticated)
┌──────────────▼─────────────────────┐
│  Agora ConvoAI API (external)      │
│  - Agent lifecycle management      │
│  - Audio/video transport           │
│  - Messaging infrastructure        │
└────────────────────────────────────┘
```

## Credential Storage

| Credential         | Stored Where        | Access                     |
| ------------------ | ------------------- | -------------------------- |
| APP_ID             | Backend `.env`      | Server-side only           |
| APP_CERTIFICATE    | Backend `.env`      | Server-side only           |
| CUSTOMER_ID/SECRET | Backend `.env`      | Server-side only           |
| TTS/ASR API keys   | Backend `.env`      | Server-side only           |
| RTC token          | Client memory (ref) | Per-session, not persisted |
| RTM token          | Client memory (ref) | Per-session, not persisted |
| Auth JWT           | Client memory (ref) | Clears on page refresh     |

## Token Generation

- **v007 tokens** — generated server-side with `APP_ID` + `APP_CERTIFICATE`
- Tokens include RTC + RTM service grants
- Tokens are short-lived; clients receive them per-session
- Fallback: Basic auth when `APP_CERTIFICATE` not available (not recommended for production)

## Secret Redaction

- Backend redacts secrets in `/start-agent?debug=1` responses
- Regex pattern: `(key|token|api_key|secret|certificate|password|authorization|credentials)`
- Strings >8 chars matching pattern: first 4 + `***` + last 4
- Curl debug dumps at `/tmp/agora_curl_*.sh` contain unredacted payloads — local access only

## Optional Authentication Layer

- **Google OAuth** — login via Google, callback to `/auth/login`
- **SMS 2FA** — Twilio-based phone verification
- **Session encryption** — encrypted session memory on disk
- **JWT tokens** — held in client memory only (not cookies, not localStorage)
- Blueprint-based Flask integration — disabled by default

## CORS Policy

- Requests with `Authorization` header: specific `Origin` + `Access-Control-Allow-Credentials: true`
- Requests without auth: `Access-Control-Allow-Origin: *`
- Preflight (`OPTIONS`) handled for all routes

## Client-Side Security

- No credentials stored in browser storage (localStorage, sessionStorage, cookies)
- Auth tokens held in React refs — cleared on page refresh
- Sensitive fields redacted in UI debug displays (6+ char strings masked)
- No user input sent directly to Agora API — always proxied through backend

## Production Recommendations

- Always use v007 tokens (not Basic auth) in production
- Set `DEBUG=false` to disable curl dump files
- Rotate `APP_CERTIFICATE` periodically
- Use HTTPS termination at nginx/load balancer level
- For Shen biomarkers: COEP/COOP/CORP headers required (configured in `next.config.ts`)

## Related Deep Dives

- None
