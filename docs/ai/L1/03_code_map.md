# 03 Code Map

> Directory map and fast guidance on where common sample-stack behavior lives.

## Key Directories

| Path | Role |
| --- | --- |
| `simple-backend/` | Python backend, token generation, agent start/stop, auth helpers |
| `react-voice-client/` | primary voice web client |
| `react-video-client-avatar/` | avatar/video web client, meeting UI |
| `simple-voice-client-no-backend/` | static demo client |
| `simple-voice-client-with-backend/` | plain JS client using backend |
| `recipes/` | scenario-focused setup docs |

## Important Backend Files

- `simple-backend/local_server.py` — main Flask app and endpoints
- `simple-backend/core/auth.py` — shared client auth/session logic
- `simple-backend/core/meeting_mode.py` — meeting join/end helpers
- `simple-backend/core/consultant_dashboard.py` — dashboard integration helpers

## Related Deep Dives

- [therapy_profile](L2/therapy_profile.md) — specific therapy stack layout across repos
