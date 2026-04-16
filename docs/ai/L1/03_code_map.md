# 03 Code Map

> Directory structure, module responsibilities, and where to find things in the multi-app repo.

## Top-Level Layout

```
agent-samples/
├── simple-backend/               # Python Flask backend (port 8082)
│   ├── local_server.py           # Flask routes and server entry
│   ├── lambda_handler.py         # AWS Lambda wrapper
│   ├── core/                     # Business logic modules
│   │   ├── config.py             # Profile-based env var loading
│   │   ├── agent.py              # Payload building + Agora API calls
│   │   ├── tokens.py             # v007 token generation (RTC+RTM)
│   │   ├── auth.py               # Optional OAuth + SMS 2FA
│   │   ├── consultant_dashboard.py  # Optional dashboard integration
│   │   ├── phone_numbers.py      # Phone validation
│   │   └── utils.py              # Shared utilities
│   ├── templates/                # HTML templates for auth pages
│   ├── tests/                    # Pytest test suite
│   └── start.sh                  # PM2 wrapper script
│
├── react-voice-client/           # React voice UI (port 8083)
│   ├── app/                      # Next.js app directory
│   │   ├── page.tsx              # Main page
│   │   ├── layout.tsx            # Root layout
│   │   └── globals.css           # Global styles
│   ├── components/
│   │   ├── VoiceClient.tsx       # Main voice component
│   │   └── ThemeToggle.tsx       # Dark/light mode
│   ├── hooks/
│   │   ├── useAgoraVoiceClient.ts     # RTC+RTM wrapper
│   │   ├── useAudioVisualization.ts   # Volume bars animation
│   │   ├── use-audio-devices.ts       # Mic selection
│   │   ├── use-is-mobile.ts           # Responsive detection
│   │   └── useAutoScroll.ts           # Transcript auto-scroll
│   └── lib/theme/                # Theme utilities
│
├── react-video-client-avatar/    # React video avatar UI (port 8084)
│   ├── (same structure as voice client)
│   ├── components/
│   │   └── VideoAvatarClient.tsx # Main video avatar component
│   ├── hooks/
│   │   ├── useAgoraVideoClient.ts     # RTC+RTM+video wrapper
│   │   └── useShenai.ts               # Video biomarkers hook
│   └── public/shenai-sdk/        # Shen.AI WASM SDK (vendored)
│
├── recipes/                      # Configuration recipes
│   ├── therapist.md              # Wellness/biomarker demo
│   └── thymia.md                 # Voice biomarker integration
│
├── design/                       # Design rationale documents
│   ├── AI_SAMPLES_DESIGN.md
│   └── AI_SAMPLES_UIKIT_TOOLKIT_DEV.md
│
├── simple-voice-client-no-backend/    # Vanilla JS client (no backend)
├── simple-voice-client-with-backend/  # Vanilla JS client (with backend)
├── ecosystem.config.js           # PM2 production config
└── session-timeline.sh           # Operational debugging script
```

## Core Files by Task

| Task                         | Start Here                                                   |
| ---------------------------- | ------------------------------------------------------------ |
| Change agent creation logic  | `simple-backend/core/agent.py`                               |
| Add a new profile variable   | `simple-backend/core/config.py`                              |
| Modify token generation      | `simple-backend/core/tokens.py`                              |
| Add a backend route          | `simple-backend/local_server.py`                             |
| Change voice UI              | `react-voice-client/components/VoiceClient.tsx`              |
| Change video avatar UI       | `react-video-client-avatar/components/VideoAvatarClient.tsx` |
| Modify RTC/RTM connection    | `*/hooks/useAgoraVoiceClient.ts` or `useAgoraVideoClient.ts` |
| Add a new recipe             | `recipes/`                                                   |
| Change production deployment | `ecosystem.config.js`                                        |
| Update backend tests         | `simple-backend/tests/`                                      |

## Backend Module Responsibilities

| Module              | Responsibility                                      |
| ------------------- | --------------------------------------------------- |
| `config.py`         | Profile-based env var loading, defaults, validation |
| `agent.py`          | Build Agora API payloads, send HTTP requests        |
| `tokens.py`         | v007 token generation with RTC+RTM services         |
| `auth.py`           | Google OAuth, SMS 2FA, encrypted session memory     |
| `local_server.py`   | Flask routes, CORS, request handling                |
| `lambda_handler.py` | AWS Lambda entry point (wraps Flask app)            |

## Related Deep Dives

- [Agent Lifecycle](deep_dives/agent_lifecycle.md) — Payload building details, vendor-specific configs
