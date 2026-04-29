# 02 Architecture

> System design overview: multi-app stack with Python backend, React clients, and Agora Conversational AI integration.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     User's Browser                            │
│                                                               │
│  ┌─────────────────────┐     ┌──────────────────────────┐   │
│  │ react-voice-client   │     │ react-video-client-avatar │   │
│  │ (Next.js, port 8083) │     │ (Next.js, port 8084)      │   │
│  │                      │     │                           │   │
│  │ - Audio capture      │     │ - Audio + video capture   │   │
│  │ - Voice visualization│     │ - Avatar rendering        │   │
│  │ - Transcript display │     │ - Biomarker panels        │   │
│  └──────────┬───────────┘     └──────────┬────────────────┘   │
│             │                            │                    │
│             └────────────┬───────────────┘                    │
│                          │ HTTP                               │
└──────────────────────────┼────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   simple-backend         │
              │   (Flask, port 8082)     │
              │                          │
              │   - Token generation     │
              │   - Agent lifecycle      │
              │   - Profile config       │
              │   - Optional auth        │
              └────────────┬────────────┘
                           │ HTTP
              ┌────────────▼────────────┐
              │   Agora ConvoAI API      │
              │                          │
              │   - Agent creation       │
              │   - STT + LLM + TTS     │
              │   - RTC audio transport  │
              │   - RTM messaging        │
              └─────────────────────────┘
```

## App Responsibilities

| App                         | Language   | Role                                  |
| --------------------------- | ---------- | ------------------------------------- |
| `simple-backend`            | Python     | Token generation, agent orchestration |
| `react-voice-client`        | TypeScript | Audio-only conversational UI          |
| `react-video-client-avatar` | TypeScript | Video avatar conversational UI        |

## Request Lifecycle

```
1. Client → GET /start-agent?channel=X&profile=VOICE
2. Backend → initialize_constants("voice")  # load profile env vars
3. Backend → build_token_with_rtm()          # v007 token generation
4. Backend → create_agent_payload()          # assemble Agora API payload
5. Backend → send_agent_to_channel()         # POST to Agora ConvoAI API
6. Backend → return {token, uid, channel, appid, agent_response}
7. Client → RTC join(channel, uid, token)    # audio/video connection
8. Client → RTM subscribe(channel)           # transcript messages
9. Client → AgoraVoiceAI.init()              # toolkit integration
10. [Conversation flows via RTC audio + RTM messages]
11. Client → GET /hangup-agent?agent_id=X
12. Backend → POST to Agora leave API
```

## SDK Layer

React clients depend on three npm packages:

| Package                      | Purpose                       |
| ---------------------------- | ----------------------------- |
| `agora-rtc-sdk-ng`           | RTC audio/video transport     |
| `agora-rtm`                  | Real-time messaging           |
| `agora-agent-client-toolkit` | Conversational AI integration |
| `@agora/agent-ui-kit`        | Pre-built UI components       |

## Key Design Decisions

- **Profile-based configuration** — backend loads env vars dynamically per request using `<PROFILE>_<VARIABLE>` pattern; supports unlimited profiles without code changes
- **Stateless backend** — no database, no session storage (except optional auth); all state lives in Agora's infrastructure
- **Async custom LLM registration** — `/register-agent` called in background thread; agent starts even if custom LLM is down
- **Memory-only auth tokens** — JWT tokens held in React refs, not localStorage; clears on page refresh for security
- **Vendor abstraction** — TTS, ASR, avatar, and MLLM vendors configured via env vars; backend builds vendor-specific payloads

## Optional Extensions

- **Custom LLM** — proxy LLM calls through your own server for augmentation
- **MCP servers** — tool calling via Model Context Protocol
- **Biomarkers** — Shen (video vitals, client-side) and Thymia (voice biomarkers, server-side)
- **Auth** — Google OAuth + SMS 2FA + encrypted session memory

## Related Deep Dives

- [Profile Configuration](L2/profile_configuration.md) — Profile system, vendor configs, MLLM setup
- [Agent Lifecycle](L2/agent_lifecycle.md) — Payload building, API calls, custom LLM registration
