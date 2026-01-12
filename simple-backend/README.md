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

The backend supports **base settings** and optional **profile settings** for running multiple configurations.

### Base Settings

**Required settings (no profile prefix):**

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

**Optional avatar settings (add to base settings for avatar support):**

```bash
AVATAR_VENDOR=  # heygen or anam
AVATAR_API_KEY= # API key from avatar provider
AVATAR_ID=      # Avatar identifier from provider
```

**TTS Voice Options:**

- **Rime**: `astra`, `deedee`, `marsh`
- **ElevenLabs**: Get from [voice library](https://elevenlabs.io/)
- **OpenAI**: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Cartesia**: Get from [voice library](https://cartesia.ai/)

**Avatar Vendors:**

- **HeyGen**: Set `AVATAR_VENDOR=heygen`
- **Anam**: Set `AVATAR_VENDOR=anam` (uses special Agora endpoint automatically)

### Profile Settings

Profiles allow running **completely separate configurations** with different credentials and vendors. When a client sends `?profile=<name>`, the backend uses only the `<NAME>_*` prefixed variables with **no fallback** to base settings.

**Profile format:** `PROFILENAME_VAR_NAME` (profile name is uppercased)

**Example: Video profile** (used by react-video-client-avatar with `?profile=video`):

```bash
# Video profile - completely separate from base settings
VIDEO_APP_ID=              # Different Agora app (e.g., beta instance)
VIDEO_APP_CERTIFICATE=     # Certificate for video app
VIDEO_AGENT_AUTH_HEADER=   # Auth header for video app
VIDEO_LLM_API_KEY=         # Different LLM API key
VIDEO_TTS_VENDOR=          # Different TTS vendor (e.g., elevenlabs)
VIDEO_TTS_KEY=             # Different TTS API key
VIDEO_TTS_VOICE_ID=        # Different voice
VIDEO_AVATAR_VENDOR=       # heygen or anam
VIDEO_AVATAR_API_KEY=      # Avatar provider API key
VIDEO_AVATAR_ID=           # Avatar identifier
```

**How profiles work:**

1. Client sends `?profile=video` (react-video-client-avatar does this automatically)
2. Backend ONLY uses `VIDEO_*` prefixed variables
3. No fallback to base variables - profile must have complete set of credentials
4. If variable missing, uses hardcoded defaults (not base settings)

**Example use cases:**

- **Base settings**: Voice-only client with Rime TTS on production Agora app
- **VIDEO profile**: Avatar client with ElevenLabs TTS on beta Agora app
- **STAGING profile**: Test environment with different credentials

This allows running multiple clients with completely isolated configurations.

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
