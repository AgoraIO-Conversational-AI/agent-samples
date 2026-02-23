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

Server runs on http://localhost:8082 (default).

## Configuration

The backend uses **profiles** to manage client configurations via environment variables.

### Default Profiles

**Voice Client** uses the `voice` profile (`VOICE_*` prefixed variables):

```bash
# Agora credentials
VOICE_APP_ID=
VOICE_APP_CERTIFICATE=
VOICE_AGENT_AUTH_HEADER=

# MLLM settings — choose one vendor:

# Option A: Gemini Live (VertexAI)
VOICE_ENABLE_MLLM=true
VOICE_MLLM_VENDOR=vertexai
VOICE_MLLM_MODEL=gemini-live-2.5-flash-preview-native-audio-09-2025
VOICE_MLLM_ADC_CREDENTIALS_STRING={"type":"service_account"...}
VOICE_MLLM_PROJECT_ID=
VOICE_MLLM_LOCATION=us-central1
VOICE_MLLM_VOICE=Charon
VOICE_MLLM_TRANSCRIBE_AGENT=true
VOICE_MLLM_TRANSCRIBE_USER=true

# Option B: OpenAI Realtime
# VOICE_ENABLE_MLLM=true
# VOICE_MLLM_VENDOR=openai
# VOICE_MLLM_MODEL=gpt-4o-realtime-preview
# VOICE_MLLM_API_KEY=sk-...
# VOICE_MLLM_STYLE=openai
# VOICE_MLLM_VOICE=alloy

# ASR and AIVAD
VOICE_ASR_VENDOR=ares
VOICE_ENABLE_AIVAD=false

# Prompts
VOICE_DEFAULT_GREETING=Hey There Sir
VOICE_DEFAULT_PROMPT=You are a friendly assistant.

# Debug
VOICE_ENABLE_CURL_DUMP=true
```

**Video Client** uses the `video` profile (`VIDEO_*` prefixed variables):

```bash
# Agora credentials
VIDEO_APP_ID=
VIDEO_APP_CERTIFICATE=
VIDEO_AGENT_AUTH_HEADER=

# LLM settings (direct OpenAI)
VIDEO_ENABLE_MLLM=false
VIDEO_LLM_API_KEY=
VIDEO_LLM_MODEL=gpt-4o

# LLM settings (custom LLM server — config only, no code changes needed)
# VIDEO_LLM_URL=https://<tunnel>.trycloudflare.com/chat/completions
# VIDEO_LLM_VENDOR=custom
# VIDEO_LLM_STYLE=openai

# TTS settings
VIDEO_TTS_VENDOR=elevenlabs
VIDEO_TTS_KEY=
VIDEO_TTS_VOICE_ID=
VIDEO_ELEVENLABS_MODEL=eleven_flash_v2_5
VIDEO_TTS_SAMPLE_RATE=24000

# ASR and AIVAD
VIDEO_ASR_VENDOR=ares
VIDEO_ENABLE_AIVAD=true

# Avatar settings
VIDEO_AVATAR_VENDOR=heygen
VIDEO_AVATAR_API_KEY=
VIDEO_AVATAR_ID=
VIDEO_HEYGEN_QUALITY=high

# Prompts
VIDEO_DEFAULT_GREETING=Hey there, I am Quiz Master Bella...
VIDEO_DEFAULT_PROMPT=You are Bella, a quiz master...

# Debug
VIDEO_ENABLE_CURL_DUMP=true
```

### Profile Overrides

Both clients have a "Server Profile" field to override the default profile. Leave empty to use defaults (`VOICE` for voice client, `VIDEO` for video client).

**Profile names are case-insensitive** - the server normalizes all profile names to lowercase, so `VOICE`, `voice`, or `Voice` all work identically.

### For AI Coding Assistants

When setting up the `.env` file:

- Voice client requires `VOICE_*` prefixed variables
- Video client requires `VIDEO_*` prefixed variables

Documentation may show simplified variable names for readability, but always use the full prefix.

### Debug Settings

When curl dump is enabled (`VOICE_ENABLE_CURL_DUMP=true` or `VIDEO_ENABLE_CURL_DUMP=true`), the backend writes timestamped shell scripts to `/tmp/`:

- Format: `agora_curl_<profile>_YYYYMMDD_HHMMSS.sh`
- Examples: `agora_curl_voice_20260120_143022.sh`, `agora_curl_video_20260120_143045.sh`

This is useful for debugging API requests. The curl dump includes full request headers and payload.

## Usage

**Start agent:**

```bash
curl "http://localhost:8082/start-agent?channel=test"
```

**Start agent with profile:**

```bash
curl "http://localhost:8082/start-agent?channel=test&profile=VIDEO"
```

**Stop agent:**

```bash
curl "http://localhost:8082/hangup-agent?agent_id=abc123"
```

**Health check:**

```bash
curl "http://localhost:8082/health"
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

## Custom LLM Server (Optional)

A Custom LLM server sits between Agora ConvoAI and your LLM provider, giving you full control over prompts, RAG, tool calling, and response formatting.

See: [server-custom-llm](https://github.com/AgoraIO-Conversational-AI/server-custom-llm)

**Configuration:** Set `LLM_URL` to your custom server endpoint and `LLM_VENDOR=custom` in `.env`:

```bash
VOICE_LLM_URL=https://your-custom-llm.example.com/chat/completions
VOICE_LLM_API_KEY=your-openai-key
VOICE_LLM_VENDOR=custom
VOICE_LLM_STYLE=openai
```

The custom server proxies requests to your LLM provider and supports endpoints for basic chat (`/chat/completions`), RAG-enhanced chat (`/rag/chat/completions`), and multimodal audio (`/audio/chat/completions`).

## MCP Memory Server (Optional)

An MCP memory server gives agents persistent per-user memory via tool calling, allowing the agent to remember context across conversations.

See: [server-mcp](https://github.com/AgoraIO-Conversational-AI/server-mcp)

**Configuration:** Set `MCP_SERVERS` as a JSON array in `.env`:

```bash
VOICE_MCP_SERVERS=[{"name":"memory","endpoint":"https://your-mcp-server.example.com/mcp","transport":"streamable_http","allowed_tools":["*"]}]
```

The MCP server must be publicly accessible. For local development, use [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to expose your local server.
