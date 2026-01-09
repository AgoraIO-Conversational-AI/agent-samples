# Simple Backend

Python backend for managing AI agents and generating RTC credentials. Supports local development, cloud instances, and AWS Lambda deployment.

> **📘 For AI Coding Assistants:** See [../AGENT.md](../AGENT.md) for comprehensive implementation guidance and API reference.

## Quick Start

**1. Install dependencies:**

```bash
pip3 install -r requirements-local.txt
```

**2. Configure `.env` file:**

Copy `.env.example` to `.env` and fill in your credentials. See [Configuration](#configuration) below.

**3. Run server:**

```bash
python3 local_server.py
# Or specify custom port:
PORT=8082 python3 local_server.py
```

Server runs on http://localhost:8081 (default).

## Configuration

The backend uses **profiles** to support multiple configurations. Each profile can override any base setting using the `PROFILENAME_VAR_NAME` format.

### Voice-Only Mode (Base Profile)

**Required for all voice clients:**

```bash
# Agora credentials
APP_ID=
APP_CERTIFICATE=
AGENT_AUTH_HEADER=

# LLM settings
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini

# TTS settings - Choose ONE vendor
TTS_VENDOR=  # rime, elevenlabs, openai, or cartesia
TTS_KEY=     # API key for your TTS vendor
TTS_VOICE_ID=  # Voice ID for your TTS vendor
```

**TTS Voice Options:**

- **Rime**: `astra`, `deedee`, `marsh`
- **ElevenLabs**: Get from [voice library](https://elevenlabs.io/)
- **OpenAI**: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Cartesia**: Get from [voice library](https://cartesia.ai/)

### Avatar Mode (Profile Example)

**For react-video-client-avatar**, add profile-specific settings to run with **completely different credentials and vendors**:

```bash
# Avatar profile overrides (accessed via ?profile=avatar)
AVATAR_APP_ID=              # Different Agora app (e.g., for beta)
AVATAR_APP_CERTIFICATE=     # Certificate for avatar app
AVATAR_AGENT_AUTH_HEADER=   # Auth header for avatar app
AVATAR_TTS_VENDOR=          # Different TTS vendor (e.g., elevenlabs)
AVATAR_TTS_KEY=             # Different TTS API key
AVATAR_TTS_VOICE_ID=        # Different voice
AVATAR_AVATAR_VENDOR=       # heygen or anam
AVATAR_AVATAR_API_KEY=      # Avatar provider API key
AVATAR_AVATAR_ID=           # Avatar identifier
```

**Avatar Vendors:**

- **HeyGen**: Set `AVATAR_AVATAR_VENDOR=heygen`
- **Anam**: Set `AVATAR_AVATAR_VENDOR=anam` (uses special Agora endpoint automatically)

**How profiles work:**

1. Client sends `?profile=avatar`
2. Backend checks `AVATAR_TTS_VENDOR`, falls back to `TTS_VENDOR`
3. Backend checks `AVATAR_APP_ID`, falls back to `APP_ID`
4. etc. for all settings

This allows running voice-only clients with Rime on one Agora app, and avatar clients with ElevenLabs on a different Agora app.

## Usage

**Start agent:**

```bash
curl "http://localhost:8081/start-agent?channel=test"
```

**Start agent with profile:**

```bash
curl "http://localhost:8081/start-agent?channel=test&profile=avatar"
```

**Stop agent:**

```bash
curl "http://localhost:8081/hangup-agent?agent_id=abc123"
```

**Health check:**

```bash
curl "http://localhost:8081/health"
```

**API Documentation:**

- [Start agent REST API](https://docs.agora.io/en/conversational-ai/rest-api/agent/join)
- [Stop agent REST API](https://docs.agora.io/en/conversational-ai/rest-api/agent/leave)

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=core --cov-report=term-missing

# Verbose
pytest -v
```

## AWS Lambda Deployment

**1. Package:**

```bash
zip -r lambda.zip lambda_handler.py core/
```

**2. Upload to AWS Lambda**

**3. Set environment variables** (same as `.env` format above)

**4. Configure API Gateway trigger**

## Advanced Configuration

See `.env.example` for all available settings including:

- ASR vendor options (Ares, Deepgram)
- VAD settings
- Vendor-specific TTS models
- Avatar quality settings
- Debug options

## Architecture

```
simple-backend/
├── core/              # Shared business logic
│   ├── config.py     # Environment variables & profiles
│   ├── tokens.py     # Token generation
│   ├── agent.py      # Agent API calls
│   └── utils.py      # Utilities
├── lambda_handler.py # AWS Lambda wrapper
├── local_server.py   # Flask development server
└── .env              # Local config (gitignored)
```
