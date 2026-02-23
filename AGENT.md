# Agent Samples — AI Coding Assistant Guide

---

## Configuration Translation Guide

### Profile-Based Variable Naming

When users provide environment variables, they are often providing the **base variable names** without the profile prefix. The backend uses a profile-based system where all variables need a `<PROFILE>_` prefix.

**Example: User provides MLLM config for VOICE profile**

```bash
# DO NOT use these directly - they need profile prefix
MLLM_LOCATION=us-central1
MLLM_VENDOR=vertexai
ENABLE_MLLM=true
APP_ID=20b7c51...
```

**CORRECT translation to .env (with VOICE\_ prefix):**

```bash
VOICE_MLLM_LOCATION=us-central1
VOICE_MLLM_VENDOR=vertexai
VOICE_ENABLE_MLLM=true
VOICE_APP_ID=20b7c51...
```

### Critical Variable Names

**LOCATION vs REGION:**

- Backend expects: `MLLM_LOCATION`
- NOT: `MLLM_REGION`

If user provides `MLLM_LOCATION=us-central1`, translate to `VOICE_MLLM_LOCATION=us-central1` (DO NOT change LOCATION to REGION!)

### Variable Naming Pattern

Profile variables follow: `<PROFILE>_<VARIABLE>` format

```bash
# CORRECT
VOICE_MLLM_VENDOR=vertexai
VOICE_MLLM_MODEL=gemini-live-2.5-flash-preview-native-audio-09-2025

# WRONG (double MLLM)
VOICE_MLLM_MLLM_VENDOR=vertexai
```

### Debugging Agent Creation Failures

**Symptom:** RTM error `-11033: user offline`

**Root cause:** Agent failed to create (400 error from Agora API)

**How to debug:**

1. Check backend logs for `Response status: 400`
2. View most recent curl dump: `ls -lt /tmp/agora_curl_*.sh | head -1`
3. Look for `"location": null` in mllm params (should be `"location": "us-central1"`)
4. Verify `"enable_mllm": true` in advanced_features

**Common causes:**

- Missing or null `location` field in MLLM config
- Invalid GCP credentials
- Wrong model name or region

### Required MLLM Variables for Gemini Live

When translating user config for VOICE profile:

```bash
VOICE_ENABLE_MLLM=true
VOICE_MLLM_VENDOR=vertexai
VOICE_MLLM_MODEL=gemini-live-2.5-flash-preview-native-audio-09-2025
VOICE_MLLM_ADC_CREDENTIALS_STRING={...GCP service account JSON...}
VOICE_MLLM_PROJECT_ID=your-gcp-project-id
VOICE_MLLM_LOCATION=us-central1  # NOT REGION!
VOICE_MLLM_VOICE=Charon
VOICE_MLLM_TRANSCRIBE_AGENT=true
VOICE_MLLM_TRANSCRIBE_USER=true
VOICE_ASR_VENDOR=ares
VOICE_ASR_LANGUAGE=en-US
VOICE_VAD_SILENCE_DURATION_MS=300
VOICE_ENABLE_AIVAD=true
```

---

## Companion Servers (Optional)

These standalone servers extend simple-backend with advanced capabilities. They are **not required** for basic operation.

- **[server-custom-llm](https://github.com/AgoraIO-Conversational-AI/server-custom-llm)** — Custom LLM proxy. Intercepts LLM requests for RAG, custom prompts, tool calling, and response formatting. Set `LLM_URL` to your server endpoint, `LLM_VENDOR=custom`.
- **[server-mcp](https://github.com/AgoraIO-Conversational-AI/server-mcp)** — MCP Memory Server. Gives agents persistent per-user memory via tool calling. Configure via `MCP_SERVERS` JSON array in `.env`.

### Port Reference

| Server     | Language | Port |
| ---------- | -------- | ---- |
| MCP Memory | Python   | 8090 |
| MCP Memory | Node.js  | 8091 |
| MCP Memory | Go       | 8092 |
| Custom LLM | Python   | 8100 |
| Custom LLM | Node.js  | 8101 |
| Custom LLM | Go       | 8102 |

### LLM Config Fields Reference

Fields supported in the LLM config block sent to Agora ConvoAI API:

| Field              | Description                                                       |
| ------------------ | ----------------------------------------------------------------- |
| `url`              | LLM endpoint URL                                                  |
| `api_key`          | API key for the LLM provider                                      |
| `style`            | Protocol style: `openai` (default), `gemini`, `anthropic`, `dify` |
| `vendor`           | `custom` (adds turn_id + timestamp), `azure` (Azure OpenAI)       |
| `greeting_configs` | Greeting behavior, e.g. `{"mode": "single_first"}`                |
| `mcp_servers`      | Array of MCP server configs for tool calling                      |

---

## Backend Configuration

The backend (`simple-backend/`) uses a **profile-based configuration system** to manage different client types and use cases.

### Default Profiles (Required)

Two profiles are required for the clients to work out of the box:

**1. `VOICE` profile** - Used by the voice client (`VOICE_*` prefixed variables)

- **Architecture**: TTS + LLM mode (Rime TTS + OpenAI LLM)
- **Key features**: Rime voice synthesis with "astra" voice, GPT-4o-mini LLM
- **Transcript delivery**: RTM stream messages with `is_final=true` for completed utterances

**2. `VIDEO` profile** - Used by the video client (`VIDEO_*` prefixed variables)

- **Architecture**: Traditional TTS + LLM stack with avatar
- **Key features**: Separate TTS (ElevenLabs), LLM (GPT-4o), avatar (HeyGen)
- **Transcript delivery**: RTM stream messages

**Note**: Profile names are **case-insensitive**. The server normalizes all profile names to lowercase, so `VOICE`, `voice`, or `Voice` all work identically. Clients default to uppercase (`VOICE`, `VIDEO`) but any case is accepted.

### Profile System Mechanics

**Environment Variable Naming:**

- Profile variables use `<PROFILE>_<VARIABLE>` format
- Example: `VOICE_APP_ID`, `VIDEO_TTS_VENDOR`, `VIDEO_AVATAR_VENDOR`
- When clients send a profile parameter, the backend loads all matching prefixed variables

**Client Behavior:**

- Voice client sends `profile=VOICE` by default (can override via "Server Profile" field)
- Video client sends `profile=VIDEO` by default (can override via "Server Profile" field)
- Empty "Server Profile" field uses the default for that client type
- Profile names are case-insensitive (server normalizes to lowercase)

**How It Works:**

1. Client makes request: `http://localhost:8082/start-agent?channel=test&profile=VOICE`
2. Backend normalizes profile to lowercase: `"VOICE"` -> `"voice"`
3. Backend calls `initialize_constants(profile="voice")` in `core/config.py`
4. Config system loads all `VOICE_*` prefixed variables from `.env`
5. Agent starts with voice profile configuration

### Transcript Configuration Differences

**MLLM Mode (Gemini Live):**

```bash
VOICE_ENABLE_MLLM=true
VOICE_MLLM_VENDOR=vertexai
VOICE_MLLM_MODEL=gemini-live-2.5-flash-preview-native-audio-09-2025
# Transcription is built-in, delivered via RTM stream messages
VOICE_MLLM_TRANSCRIBE_AGENT=true  # Agent speech transcription
VOICE_MLLM_TRANSCRIBE_USER=true   # User speech transcription
```

**TTS+LLM Mode (Traditional):**

```bash
VIDEO_ENABLE_MLLM=false
VIDEO_LLM_MODEL=gpt-4o
VIDEO_TTS_VENDOR=elevenlabs
VIDEO_AVATAR_VENDOR=heygen
# Transcription delivered in start-agent API response
VIDEO_MLLM_TRANSCRIBE_AGENT=true  # Required for agent transcript
VIDEO_MLLM_TRANSCRIBE_USER=true   # Required for user transcript
```

### Active Profiles

- `voice` - Default for voice client (MLLM/Gemini Live)
- `video` - Default for video client (TTS+LLM+HeyGen)
- `video_anam` - Alternative with Anam avatar
- `video_heygen` - Alternative HeyGen configuration
- `video_mllm_heygen` - MLLM mode with HeyGen avatar

---

## Local Development Quick Start

### Prerequisites

- Node.js >= 20.9.0 (required by Next.js 16). Run `nvm use` in the repo root — the `.nvmrc` file selects the correct version automatically.
- Python 3.x

### Step 1: Start the backend

```bash
cd simple-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-local.txt
cp .env.example .env
# Edit .env — fill in credentials (see Backend Configuration section above)
python3 local_server.py
```

### Step 2: Start a frontend client

**Voice client:**

```bash
cd react-voice-client
npm install --legacy-peer-deps
npm run dev
# Open http://localhost:8083
```

**Video avatar client:**

```bash
cd react-video-client-avatar
npm install --legacy-peer-deps
npm run dev
# Open http://localhost:8084
```

---

## Production Deployment (EC2 + nginx on port 443)

This section documents how to serve all agent-samples behind nginx on port 443 alongside an existing application, using path-based routing.

### Architecture

```
nginx :443 (convoai-demo.agora.io)
  /                              -> /var/www/palabra/         (existing SPA)
  /v1/, /query, /oauth, /pstn   -> localhost:7080             (existing API)
  /simple-backend/               -> localhost:8082             (Flask API, prefix stripped)
  /react-voice-client/           -> localhost:8083             (Next.js voice client)
  /react-video-client-avatar/    -> localhost:8084             (Next.js video+avatar client)
  /simple-voice-client-no-backend/     -> static files via alias
  /simple-voice-client-with-backend/   -> static files via alias
```

### Source Code Changes (backward-compatible)

Two env-var-driven configs were added. When env vars are **not set** (local dev), behavior is identical to the original code.

**`next.config.ts`** (both `react-voice-client` and `react-video-client-avatar`):

```typescript
const nextConfig: NextConfig = {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  typescript: { ignoreBuildErrors: true },
  transpilePackages: ["@agora/conversational-ai", "@agora/agent-ui-kit"],
};
```

- `basePath` makes Next.js serve all routes/assets under the specified prefix
- `typescript.ignoreBuildErrors` bypasses an unused `@ts-expect-error` in `@agora/agent-ui-kit`

**`VoiceClient.tsx` / `VideoAvatarClient.tsx`**:

```typescript
const DEFAULT_BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8082";
```

- When `NEXT_PUBLIC_BACKEND_URL=/simple-backend` is set at build time, the browser makes relative requests to the same origin
- When not set, defaults to `http://localhost:8082` for local dev

### Step 1: Python Backend Setup

```bash
cd simple-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-local.txt
cp .env.example .env
# Edit .env with real Agora, LLM, TTS, and avatar credentials
```

Create `simple-backend/start.sh` (PM2 workaround for Python):

```bash
#!/bin/bash
cd /home/ubuntu/agent-samples/simple-backend
source venv/bin/activate
PORT=8082 exec python3 local_server.py
```

```bash
chmod +x start.sh
```

### Step 2: Build Next.js Apps

```bash
# Voice client
cd react-voice-client
npm install --legacy-peer-deps
NEXT_PUBLIC_BASE_PATH=/react-voice-client NEXT_PUBLIC_BACKEND_URL=/simple-backend npm run build

# Video avatar client
cd ../react-video-client-avatar
npm install --legacy-peer-deps
NEXT_PUBLIC_BASE_PATH=/react-video-client-avatar NEXT_PUBLIC_BACKEND_URL=/simple-backend npm run build
```

### Step 3: PM2 Ecosystem Config

Create `ecosystem.config.js` in the repo root:

```javascript
module.exports = {
  apps: [
    {
      name: "simple-backend",
      script: "/home/ubuntu/agent-samples/simple-backend/start.sh",
      interpreter: "bash",
      watch: false,
      max_memory_restart: "200M",
    },
    {
      name: "react-voice-client",
      cwd: "/home/ubuntu/agent-samples/react-voice-client",
      script: "node_modules/.bin/next",
      args: "start -p 8083",
      env: {
        NODE_ENV: "production",
        PORT: 8083,
        NEXT_PUBLIC_BASE_PATH: "/react-voice-client",
        NEXT_PUBLIC_BACKEND_URL: "/simple-backend",
      },
      watch: false,
      max_memory_restart: "500M",
    },
    {
      name: "react-video-client-avatar",
      cwd: "/home/ubuntu/agent-samples/react-video-client-avatar",
      script: "node_modules/.bin/next",
      args: "start -p 8084",
      env: {
        NODE_ENV: "production",
        PORT: 8084,
        NEXT_PUBLIC_BASE_PATH: "/react-video-client-avatar",
        NEXT_PUBLIC_BACKEND_URL: "/simple-backend",
      },
      watch: false,
      max_memory_restart: "500M",
    },
  ],
};
```

**Critical:** The `NEXT_PUBLIC_BASE_PATH` env var must be set at **both** build time and runtime. `next start` re-reads `next.config.ts` at startup, so the PM2 env must match the build env. Without this, basePath evaluates to `""` at runtime and all pages return 404.

```bash
pm2 start ecosystem.config.js
pm2 save
```

### Step 4: Nginx Configuration

Add these location blocks **before** the catch-all `location /` block:

```nginx
    # --- Agent Samples ---

    # Flask backend (strip /simple-backend prefix via trailing slash on proxy_pass)
    location /simple-backend/ {
        proxy_pass http://localhost:8082/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Next.js voice client (^~ prevents regex cache block from stealing .js/.css)
    location ^~ /react-voice-client {
        proxy_pass http://localhost:8083;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Next.js video avatar client (^~ prevents regex cache block from stealing .js/.css)
    location ^~ /react-video-client-avatar {
        proxy_pass http://localhost:8084;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static HTML clients
    location ^~ /simple-voice-client-no-backend/ {
        alias /home/ubuntu/agent-samples/simple-voice-client-no-backend/;
        index index.html;
    }

    location ^~ /simple-voice-client-with-backend/ {
        alias /home/ubuntu/agent-samples/simple-voice-client-with-backend/;
        index index.html;
    }
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Step 5: File Permissions

```bash
chmod o+x /home/ubuntu /home/ubuntu/agent-samples
chmod -R o+r /home/ubuntu/agent-samples/simple-voice-client-no-backend/
chmod -R o+r /home/ubuntu/agent-samples/simple-voice-client-with-backend/
```

### Verification

```bash
curl -s https://convoai-demo.agora.io/simple-backend/health
# {"service":"agora-convoai-backend","status":"ok"}

curl -s -o /dev/null -w "%{http_code}" https://convoai-demo.agora.io/react-voice-client
# 200

curl -s -o /dev/null -w "%{http_code}" https://convoai-demo.agora.io/react-video-client-avatar
# 200

curl -s -o /dev/null -w "%{http_code}" https://convoai-demo.agora.io/simple-voice-client-no-backend/
# 200

curl -s -o /dev/null -w "%{http_code}" https://convoai-demo.agora.io/simple-voice-client-with-backend/
# 200
```

### Key Gotchas

1. **`^~` on proxy locations is required.** Without it, an existing `location ~* \.(js|css|...)$` regex block for static asset caching will intercept Next.js `_next/static/` requests and look for them in the wrong root directory, returning 404.

2. **PM2 Python interpreter bug.** PM2 ignores the `interpreter` field for Python scripts and wraps them in its JS `ProcessContainerFork.js`, which Python then tries to parse as Python code. Workaround: use a bash shell script that activates the venv and runs Python directly.

3. **`NEXT_PUBLIC_*` env vars must be set at runtime too.** `next start` re-evaluates `next.config.ts` at startup. If `NEXT_PUBLIC_BASE_PATH` is only set during `npm run build` but not when `next start` runs (e.g., via PM2), basePath evaluates to `""` at runtime and all pages return 404 despite being correctly built.

4. **Trailing slash on `proxy_pass` for Flask.** `location /simple-backend/` paired with `proxy_pass http://localhost:8082/;` (note trailing `/`) strips the `/simple-backend/` prefix. Flask routes are `/start-agent`, not `/simple-backend/start-agent`.

5. **No changes needed for local dev.** When no `NEXT_PUBLIC_*` env vars are set, basePath defaults to `""` and backend URL defaults to `http://localhost:8082` — identical to the original behavior.
