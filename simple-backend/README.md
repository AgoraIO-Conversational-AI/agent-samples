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
# Avatar profile overrides (accessed via ?profile=video)
VIDEO_APP_ID=              # Different Agora app (e.g., for beta)
VIDEO_APP_CERTIFICATE=     # Certificate for avatar app
VIDEO_AGENT_AUTH_HEADER=   # Auth header for avatar app
VIDEO_TTS_VENDOR=          # Different TTS vendor (e.g., elevenlabs)
VIDEO_TTS_KEY=             # Different TTS API key
VIDEO_TTS_VOICE_ID=        # Different voice
VIDEO_AVATAR_VENDOR=       # heygen or anam
VIDEO_AVATAR_API_KEY=      # Avatar provider API key
VIDEO_AVATAR_ID=           # Avatar identifier
```

**Avatar Vendors:**

- **HeyGen**: Set `VIDEO_AVATAR_VENDOR=heygen`
- **Anam**: Set `VIDEO_AVATAR_VENDOR=anam` (uses special Agora endpoint automatically)

**How profiles work:**

1. Client sends `?profile=video`
2. Backend ONLY uses VIDEO\_\* prefixed variables (no fallback to base)
3. Video profile requires complete set of VIDEO\_\* credentials

**NOTE:** Video profile does NOT fall back to base variables. You must provide all required VIDEO\_\* settings.

This allows running voice-only clients and video avatar clients with completely separate configurations.

## Usage

**Start agent:**

```bash
curl "http://localhost:8081/start-agent?channel=test"
```

**Start agent with profile:**

```bash
curl "http://localhost:8081/start-agent?channel=test&profile=video"
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
