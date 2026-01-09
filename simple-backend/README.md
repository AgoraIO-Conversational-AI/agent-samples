# Simple Backend

Python backend for managing AI agents and generating RTC credentials. Supports
local development, cloud instances, and AWS Lambda deployment.

> **📘 For AI Coding Assistants:** See [../AGENT.md](../AGENT.md) for comprehensive implementation guidance and API reference.

## Table of Contents

- [Configuration for Client Types](#configuration-for-client-types)
  - [Voice Client Mode](#voice-client-mode)
  - [Avatar Video Client Mode](#avatar-video-client-mode)
- [Usage](#usage)
  - [Local Development](#local-development)
  - [AWS Lambda Deployment](#aws-lambda-deployment)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Running Tests](#running-tests)
- [Profile Support](#profile-support)
- [Curl Request Dumps](#curl-request-dumps)

## Configuration for Client Types

Choose your configuration based on which client you're running.

### Voice Client Mode

**For:** `react-voice-client`, `simple-voice-client`, `complete-voice-client`

**Required credentials:**

```bash
# Agora settings
APP_ID=YOUR_AGORA_APP_ID
APP_CERTIFICATE=YOUR_AGORA_APP_CERTIFICATE  # Optional for testing
AGENT_AUTH_HEADER=YOUR_AGORA_AUTH_HEADER

# LLM settings
LLM_API_KEY=YOUR_OPENAI_API_KEY

# TTS settings - Choose ONE vendor and provide all three values
TTS_VENDOR=  # Required: rime, elevenlabs, openai, or cartesia
TTS_KEY=  # Required: API key for your chosen TTS vendor
TTS_VOICE_ID=  # Required: Voice/speaker ID for your chosen vendor
```

**TTS Voice Options by Vendor:**

- **Rime**: `astra`, `deedee`, `marsh` - Get TTS_KEY from [Rime](https://rime.ai/)
- **ElevenLabs**: Get voice ID from [voice library](https://elevenlabs.io/)
- **OpenAI**: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Cartesia**: Get voice ID from [voice library](https://cartesia.ai/)

### Avatar Video Client Mode

**For:** `react-video-client-avatar`

**Required: All Voice Client credentials above, PLUS avatar provider credentials**

**Choose HeyGen OR Anam:**

**Option 1: HeyGen Avatar**

```bash
# Add to your .env file (in addition to voice client settings)
AVATAR_ENABLED=true
AVATAR_VENDOR=heygen
HEYGEN_API_KEY=YOUR_HEYGEN_KEY
HEYGEN_AVATAR_ID=Wayne_20240711  # Get from HeyGen avatar library
```

**Option 2: Anam Avatar (Beta)**

```bash
# Add to your .env file (in addition to voice client settings)
AVATAR_ENABLED=true
AVATAR_VENDOR=anam
ANAM_API_KEY=YOUR_ANAM_KEY
ANAM_AVATAR_ID=YOUR_ANAM_AVATAR_ID
ANAM_BETA_APP_ID=YOUR_BETA_APP_ID
ANAM_BETA_CREDENTIALS=YOUR_BETA_CREDENTIALS
ANAM_BETA_ENDPOINT=https://api-test.agora.io/api/conversational-ai-agent/v2/projects
```

**Note:** Without avatar credentials, the video client works in voice-only mode with local camera preview but no avatar video stream.

## Usage

### Local Development

**1. Install dependencies:**

```bash
pip3 install -r requirements-local.txt
```

**2. Configure environment:**

Create `.env` file with your credentials based on which client you're running:

- For voice clients, see [Voice Client Mode](#voice-client-mode) configuration above
- For avatar video client, see [Avatar Video Client Mode](#avatar-video-client-mode) configuration above

See `.env.example` in this directory for all available configuration options and examples.

**3. Run server:**

```bash
python3 local_server.py
# Or specify custom port:
PORT=8082 python3 local_server.py
```

Server runs on http://localhost:8081 (default) or custom port via `PORT` env
var.

**4. Test the endpoints:**

**Start agent in channel:**

```bash
curl "http://localhost:8081/start-agent?channel=test"
```

Response includes `agent_id` needed for stopping the agent:

```json
{
  "channel": "test",
  "appid": "YOUR_APP_ID",
  "token": "...",
  "uid": "101",
  "agent_response": {
    "status_code": 200,
    "response": "{\"agent_id\":\"abc123...\"}"
  }
}
```

**Stop agent:**

```bash
# Use agent_id from start response
curl "http://localhost:8081/hangup-agent?agent_id=abc123"
```

**Other examples:**

```bash
# Token-only mode (no agent started)
curl "http://localhost:8081/start-agent?channel=test&connect=false"

# With profile override
curl "http://localhost:8081/start-agent?channel=test&profile=sales"

# Health check
curl "http://localhost:8081/health"
```

**API Documentation:**

- **[start agent](https://docs.agora.io/en/conversational-ai/rest-api/agent/join)** -
  API docs to start an AI Agent
- **[stop agent](https://docs.agora.io/en/conversational-ai/rest-api/agent/leave)** -
  API docs to stop an AI Agent

### AWS Lambda Deployment

**1. Package for Lambda:**

```bash
zip -r lambda.zip lambda_handler.py core/
```

**2. Upload to AWS Lambda**

**3. Set environment variables in Lambda console:**

- `APP_ID`
- `APP_CERTIFICATE`
- `AGENT_AUTH_HEADER`
- `LLM_API_KEY`
- `TTS_VENDOR`
- `TTS_KEY` (API key for chosen TTS vendor)
- See `.env.example` for all options

**4. Configure API Gateway trigger**

## Architecture

```
simple-backend/
├── core/              # Shared business logic
│   ├── config.py     # Environment variables
│   ├── tokens.py     # v007 token generation
│   ├── agent.py      # Agent API calls
│   └── utils.py      # Utilities
├── lambda_handler.py # AWS Lambda wrapper
├── local_server.py   # Flask development server
└── .env              # Local config (gitignored)
```

Core modules work identically in both Lambda and local environments.

## Running Tests

The backend includes a comprehensive test suite using pytest with unit and
integration tests.

**Run all tests:**

```bash
pytest
```

**Run with coverage:**

```bash
pytest --cov=core --cov-report=term-missing
```

**Run only unit tests:**

```bash
pytest -m unit
```

**Run only integration tests:**

```bash
pytest -m integration
```

**Run with verbose output:**

```bash
pytest -v
```

**Test Structure:**

```
tests/
├── conftest.py              # Fixtures and configuration
├── test_utils.py            # core/utils.py tests
├── test_tokens.py           # core/tokens.py tests
├── test_agent.py            # core/agent.py tests
├── test_config.py           # core/config.py tests
└── integration/
    └── test_endpoints.py    # Flask endpoint tests
```

## Profile Support

Override config per use case using profile-specific environment variables:

```bash
# Set profile-specific env vars (PREFIX_VAR_NAME format)
AVATAR_TTS_VENDOR=elevenlabs
AVATAR_TTS_KEY=sk_your_elevenlabs_key
AVATAR_TTS_VOICE_ID=cgSgspJ2msm6clMCkdW9
AVATAR_DEFAULT_PROMPT=You are a helpful avatar assistant...
AVATAR_APP_ID=your_beta_app_id
AVATAR_AGENT_AUTH_HEADER=Basic your_beta_credentials

# Use profile parameter
curl "http://localhost:8081/start-agent?channel=test&profile=avatar"
```

Variables checked in order:

1. `PROFILE_VAR_NAME` (e.g., `AVATAR_TTS_VENDOR` for profile=avatar)
2. `VAR_NAME` (base variable, e.g., `TTS_VENDOR`)
3. Default value (hardcoded)

**Common use cases:**

- **Avatar clients**: Separate APP_ID, TTS vendor, voice settings
- **A/B testing**: Different prompts, voices, or models per profile
- **Multi-tenant**: Isolate credentials per customer

**Important:** Profile names are automatically uppercased. `profile=avatar`
looks for `AVATAR_*` variables.

## Curl Request Dumps

Optional debugging feature that saves agent requests as executable curl scripts
to `/tmp/`. **Disabled by default** to avoid exposing API keys in logs.

**Enable in .env:**

```bash
ENABLE_CURL_DUMP=true
```

**Usage:**

```bash
# Find latest curl dump
ls -t /tmp/agora_curl_*.sh | head -1

# Execute the curl directly
bash /tmp/agora_curl_20260107_151440.sh
```

Each file includes timestamp, channel name, complete curl command with headers,
and prettified JSON payload.

**Note:** `.env` changes require server restart. Flask auto-reload only watches
Python files.
