# 06 Interfaces

> Boundary contracts for the backend endpoints and profile-driven behavior.

## Key Backend Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /start-agent` | start agent or return token-only response |
| `GET /hangup-agent` | stop a running agent |
| `POST /speak` | push direct TTS text to a running agent |
| `POST /join-meeting` | authorize and mint meeting credentials |
| `POST /meeting-participant-event` | notify meeting participant state |

## Common URL Parameters for `/start-agent`

| Param | Effect | Defined in |
| --- | --- | --- |
| `profile` | Selects which `{PROFILE}_*` env vars to use. Defaults vary per client. | `core/config.py` |
| `channel` | RTC channel name. Auto-generated if omitted. | `local_server.py` |
| `connect=false` | Token-only mode — generate tokens, skip ConvoAI `/join` and xhandle resolution. | `local_server.py` |
| `prompt`, `greeting` | Override profile `DEFAULT_PROMPT` / `DEFAULT_GREETING`. | `core/agent.py` |
| `voice_id` | Overrides TTS voice or, in MLLM mode, `mllm.params.voice`. | `core/agent.py` |
| `avatar_id` | Overrides `{PROFILE}_AVATAR_ID`. | `core/agent.py` |
| `xhandle` | Generates persona prompt + greeting (+ avatar image, where applicable) from a public X handle. Replaces the profile default prompt. Skipped on `connect=false`. Falls back to profile defaults on X API error. | `x/profile_prompt.py` |
| `turn_detection_mode` | xAI only: `server_vad` (default — matches xAI's native behavior) or `agora_vad`. Emitted under `mllm.turn_detection`. | `core/agent.py` |
| `turn_detection_threshold` / `_prefix_padding_ms` / `_silence_duration_ms` / `_interrupt_duration_ms` | xAI tunables; defaults match Agora's xAI docs. | `core/agent.py` |

## Profile-Level Behavior

| Env (profile-prefixed) | Default | Effect |
| --- | --- | --- |
| `IDLE_TIMEOUT` | `120` | Seconds of inactivity before ConvoAI ends the call internally. |
| `MAX_CALL_DURATION_SECONDS` | `300` | Wall-clock cap. Backend schedules an auto-hangup at this time; cancelled by manual `/hangup-agent`. Server-initiated hangups cause the client's RTC `user-left` event to fire `handleStop`. |
| `ENABLE_CURL_DUMP` | `false` | When `true`, every `/start-agent` writes a replayable curl script to `/tmp/agora_curl_<profile>_<timestamp>.sh`. |

## Contract Patterns

- profile selected by query param or client default
- backend returns channel/token/RTM details plus feature flags
- backend response includes `debug.agent_payload` when `debug=true` is set (clients use this to surface resolved prompt + greeting in `SessionInfoPanel`); sensitive fields are redacted client-side via `redactSensitiveFields()` before display
- meeting mode contracts depend on consultant-dashboard internal APIs

## Related Deep Dives

- [therapy_profile](L2/therapy_profile.md) — therapy / biomarker / dashboard-backed sample stack
- [xai_profile](L2/xai_profile.md) — xAI Grok Realtime profiles (XLS / X), xhandle persona, xAI turn detection
