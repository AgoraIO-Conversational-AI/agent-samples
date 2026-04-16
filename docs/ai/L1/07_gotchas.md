# 07 Gotchas

> Critical gotchas, tribal knowledge, and non-obvious behaviors across the sample stack.

## Backend Gotchas

### Python Output Buffering (Critical)

- Without `python3 -u` or `PYTHONUNBUFFERED=1`, stdout buffers and logs never appear
- Affects all process managers: local dev, PM2, systemd, Lambda
- Agent IDs, API response codes, and error messages silently disappear

### MLLM Variable Naming (Critical)

- Correct: `VOICE_MLLM_LOCATION=us-central1`
- WRONG: `VOICE_MLLM_REGION=us-central1` — Agora API expects LOCATION, not REGION
- WRONG: `VOICE_MLLM_MLLM_VENDOR=vertexai` — double MLLM prefix

### Profile Prefix Pattern

- Pattern: `<PROFILE>_<VARIABLE>` — single underscore between profile and variable
- No fallback: if `VOICE_APP_ID` is empty, does NOT fall back to `APP_ID`
- Case-insensitive: VOICE, voice, Voice all normalize to lowercase internally

### Avatar Sample Rates

- Akool avatars ONLY support 16kHz audio — set `TTS_SAMPLE_RATE=16000`
- Others (HeyGen, Anam) support 24kHz (ElevenLabs default) or 16kHz
- Mismatch causes audio playback distortion

### Custom LLM Registration Is Non-Blocking

- `/register-agent` called in background thread (`daemon=True`)
- If custom-llm server is down, agent still starts — request silently fails
- Response sent to client before registration attempt completes

### Pipeline Mode Transcript

- `parameters.transcript` is connection-level (NOT in pipeline config)
- Without it, agent transcript messages are NOT delivered via RTM
- User transcript may still appear (from ASR) but agent responses are missing

## Frontend Gotchas

### RTM Console Error Noise

- Agora RTM SDK logs "joinPresenceColl error: Presence service not connected"
- App does not use presence; this is SDK noise
- Suppressed in `useAgoraVideoClient.ts` via console.error override

### Audio Track Cleanup Order

- Must call `rtcClient.unsubscribe(user, "audio")` BEFORE updating React state
- Otherwise: track still playing while state updated → audio glitches

### Auth Token Persistence

- Tokens held in memory (`authTokenRef`), NOT in localStorage/sessionStorage
- On page refresh, user must re-authenticate
- Design decision: security over convenience (prevents cross-user access)

### Audio Visualization Threshold

- If threshold ≥1.0, bars never light up
- If threshold = 0, bars always active (no volume detection)
- Default 0.15 = require 15% volume before visualization shows

### Mic Selection Persistence

- Selected mic stored in localStorage as `selectedMicId`
- If device removed/unplugged, subsequent uses fail silently
- No error recovery — user must manually select a new mic

### Build-Time Environment Variables

- `NEXT_PUBLIC_*` env vars evaluated at **build time**, not runtime
- `NEXT_PUBLIC_BASE_PATH` must be set at both build AND `next start` time
- If only set at build, basePath evaluates to `""` at runtime → 404 on all pages

## Production Deployment Gotchas

### Nginx Prefix Stripping

- `location /simple-backend/` with `proxy_pass http://localhost:8082/;` (trailing slash)
- Strips `/simple-backend/` prefix before forwarding to Flask
- Flask routes are `/start-agent`, NOT `/simple-backend/start-agent`

### PM2 Python Interpreter Bug

- PM2 ignores `interpreter: "bash"` for Python scripts
- Wraps in JS ProcessContainerFork.js → Python fails to parse JS
- Workaround: use bash wrapper script (`start.sh`) instead

### SharedArrayBuffer for Shen Biomarkers

- Shen.AI WASM SDK requires SharedArrayBuffer
- Needs COEP, COOP, CORP headers (configured in `next.config.ts`)
- Missing headers: Shen crashes silently (browser disables SharedArrayBuffer)

## Debugging

### Curl Debug Dumps

- Backend saves timestamped curl scripts to `/tmp/agora_curl_*_YYYYMMDD_HHMMSS.sh`
- View most recent: `ls -lt /tmp/agora_curl_*.sh | head -1`
- Contains full request/response payload (unredacted)

### Agent Creation 400 Errors

- Symptom: agent fails, RTM error `-11033: user offline`
- Root cause: Agora API returned 400
- Debug: check `"location": null` in MLLM params → `MLLM_LOCATION` not set

## Related Deep Dives

- [Profile Configuration](deep_dives/profile_configuration.md) — Variable naming gotchas in detail
- [Agent Lifecycle](deep_dives/agent_lifecycle.md) — API error patterns
