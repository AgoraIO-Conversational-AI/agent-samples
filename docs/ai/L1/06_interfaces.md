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

## Contract Patterns

- profile selected by query param or client default
- backend returns channel/token/RTM details plus feature flags
- meeting mode contracts depend on consultant-dashboard internal APIs

## Related Deep Dives

- [therapy_profile](L2/therapy_profile.md) — sample contract extensions for therapy mode
