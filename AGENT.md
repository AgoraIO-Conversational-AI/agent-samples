# Agent Video Avatar - Session Notes

---

## ⚠️ IMPORTANT: Configuration Translation Guide for AI Assistants

### Profile-Based Variable Naming

When users provide environment variables, they are often providing the **base variable names** without the profile prefix. The backend uses a profile-based system where all variables need a `<PROFILE>_` prefix.

**Example: User provides MLLM config for VOICE profile**

```bash
# ❌ DO NOT use these directly - they need profile prefix
MLLM_LOCATION=us-central1
MLLM_VENDOR=vertexai
ENABLE_MLLM=true
APP_ID=20b7c51...
```

**✅ CORRECT translation to .env (with VOICE\_ prefix):**

```bash
VOICE_MLLM_LOCATION=us-central1
VOICE_MLLM_VENDOR=vertexai
VOICE_ENABLE_MLLM=true
VOICE_APP_ID=20b7c51...
```

### Critical Variable Names

**⚠️ LOCATION vs REGION:**

- Backend expects: `MLLM_LOCATION`
- NOT: `MLLM_REGION`

If user provides `MLLM_LOCATION=us-central1`, translate to `VOICE_MLLM_LOCATION=us-central1` (DO NOT change LOCATION to REGION!)

### Variable Naming Pattern

Profile variables follow: `<PROFILE>_<VARIABLE>` format

```bash
# ✅ CORRECT
VOICE_MLLM_VENDOR=vertexai
VOICE_MLLM_MODEL=gemini-live-2.5-flash-preview-native-audio-09-2025

# ❌ WRONG (double MLLM)
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

- **[server-custom-llm](https://github.com/AgoraIO-Community/server-custom-llm)** — Custom LLM proxy. Intercepts LLM requests for RAG, custom prompts, tool calling, and response formatting. Set `LLM_URL` to your server endpoint, `LLM_VENDOR=custom`.
- **[server-mcp-memory](https://github.com/AgoraIO-Community/server-mcp-memory)** — MCP Memory Server. Gives agents persistent per-user memory via tool calling. Configure via `MCP_SERVERS` JSON array in `.env`.

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

## Current Status (2026-01-20)

### ✅ WORKING

- **Remote video (avatar) displays correctly** - HeyGen avatar video now shows
- Audio transcription working
- Voice interaction working

### ✅ All Issues Resolved

All previously reported issues have been fixed:

1. **Local video reconnect** - ✅ Fixed via RTCHelper video track lifecycle management
2. **Chat display** - ✅ Fixed via proper transcript rendering

---

## Changes Made Today

### 1. Enhanced RTCHelper for Video Support

**File:** `react-video-client-avatar/node_modules/@agora/conversational-ai/packages/conversational-ai/helper/rtc.ts`

**Changes:**

- Added optional subscription filter callbacks to `init()`:
  ```typescript
  shouldSubscribeAudio?: (uid: number) => boolean
  shouldSubscribeVideo?: (uid: number) => boolean
  ```
- Modified `setupEventListeners()` to handle BOTH audio and video in `user-published` handler
- Default behavior: Subscribe to all audio and all video
- Added video event emission via `RTCHelperEvents.USER_PUBLISHED` for video mediaType

**Why:** RTCHelper was originally audio-only for voice clients. It ignored video `user-published` events. This made it inconsistent and forced us to bypass RTCHelper and listen to raw RTC client events directly.

**Result:** Now audio and video are handled consistently through the same event system.

---

### 2. Updated useAgoraVideoClient Hook

**File:** `react-video-client-avatar/hooks/useAgoraVideoClient.ts`

**Changes:**

- Changed from listening to raw `rtcHelper.client` events to `RTCHelper` events
- Removed manual video subscription code
- Now uses unified event handlers for both audio and video through RTCHelper
- Events: `USER_PUBLISHED`, `USER_UNPUBLISHED`, `USER_LEFT`

**Before (broken):**

```typescript
// Had to bypass RTCHelper and listen to raw RTC client
rtcHelper.client.on("user-published", async (user, mediaType) => {
  if (mediaType === "video") {
    await rtcHelper.client.subscribe(user, "video");
    setRemoteVideoTrack(user.videoTrack);
  }
});
```

**After (clean):**

```typescript
// RTCHelper handles both audio and video consistently
rtcHelper.on(RTCHelperEvents.USER_PUBLISHED, (user, mediaType) => {
  if (mediaType === "video") {
    setRemoteVideoTrack(user.videoTrack);
  }
});
```

---

## Architecture Summary

### RTCHelper Purpose

- **Voice-focused wrapper** around Agora RTC SDK for Conversational AI
- Provides:
  - Audio/video subscription automation
  - Volume monitoring for audio levels
  - Audio PTS emission for transcript sync
  - Stream message handling (receives transcript data from AI agent)
  - Connection state management
  - Singleton pattern

### Why We Enhanced It (Instead of Bypassing)

1. **Consistency** - Audio and video treated identically
2. **Simplicity** - One place to control subscriptions (init config)
3. **Integration** - Still get transcript sync, volume monitoring, AI features
4. **Flexibility** - Can filter subscriptions by UID if needed
5. **Maintainability** - All RTC logic in one place

### Current Architecture

- **One RTC SDK client instance**: Created by RTCHelper (`rtcHelper.client`)
- **One RTCHelper instance**: Singleton pattern
- **RTCHelper now handles**: Both audio and video subscriptions + events
- **Hook subscribes to**: RTCHelper events (not raw RTC client events)

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

1. Client makes request: `http://localhost:8081/start-agent?channel=test&profile=VOICE`
2. Backend normalizes profile to lowercase: `"VOICE"` → `"voice"`
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

### Profile System Cleanup (2026-01-20)

**Changes Made:**

- Voice client now sends `profile=VOICE` by default (previously sent no profile)
- Video client now sends `profile=VIDEO` by default
- Both clients use "Server Profile" UI field with appropriate placeholders
- Server implements case-insensitive profile handling (normalizes to lowercase)
- Updated all documentation to reference uppercase profile names
- Curl dump files now include profile name: `agora_curl_<profile>_YYYYMMDD_HHMMSS.sh`
- `.env` cleaned up to remove legacy profiles (AVATAR, old VIDEO, VOICETTS)
- Profile name stored in `constants["PROFILE_NAME"]` for debugging/logging

**Current Active Profiles in .env:**

- `voice` - Default for voice client (MLLM/Gemini Live)
- `video` - Default for video client (TTS+LLM+HeyGen)
- `video_anam` - Alternative with Anam avatar
- `video_heygen` - Alternative HeyGen configuration
- `video_mllm_heygen` - MLLM mode with HeyGen avatar

---

## Root Cause of Original Video Bug

**The Issue:**
RTCHelper's `user-published` handler at line 143-160 ONLY handled audio:

```typescript
this.client.on("user-published", async (user, mediaType) => {
  if (mediaType === "audio") {
    // ... subscribe and emit event
  }
  // NO ELSE BLOCK FOR VIDEO - video events were ignored!
});
```

**What was happening:**

1. Agora RTC SDK fires `user-published` for BOTH audio AND video
2. RTCHelper subscribed to audio automatically
3. RTCHelper **ignored** video events completely (no else block)
4. Our app listening to RTCHelper events never received video notifications
5. No video subscription → no video track → no video display

**The Fix:**
Added video handling in RTCHelper so both media types are treated consistently.

---

## Voice Client Compatibility ✅

**Question:** Will voice client need update for new RTCHelper changes?

**Answer:** NO - Voice client is fully compatible and does not need updates.

**Why:**

1. **Backward compatible defaults**: The new `shouldSubscribeAudio` and `shouldSubscribeVideo` callbacks are **optional** parameters
2. **Default behavior unchanged**: When omitted, RTCHelper defaults to `true` (subscribe to all audio/video)
3. **No breaking changes**: Existing voice client code at `react-voice-client/hooks/useAgoraVoiceClient.ts` still calls:
   ```typescript
   await rtcHelper.init({
     appId: config.appId,
     channel: config.channel,
     token: config.token,
     uid: config.uid,
     // No filter callbacks - defaults to subscribe all
   });
   ```
4. **Video handling is transparent**: Even though RTCHelper now handles video events, voice clients never publish video, so those events never fire
5. **Event handlers unchanged**: Voice client still listens to `RTCHelperEvents.USER_PUBLISHED` for audio only - video events are ignored in the handler

**Verification:** Checked `react-voice-client/hooks/useAgoraVoiceClient.ts` (lines 48-54) - it only handles audio mediaType, ignoring video:

```typescript
const handleUserPublished = (user: any, mediaType: "audio" | "video") => {
  if (mediaType === "audio" && user.audioTrack) {
    // ... handle audio
  }
  // Video events ignored - no else block needed
};
```

**Conclusion:** RTCHelper enhancement is 100% backward compatible. Voice client works unchanged.

---

## Next Steps (Not Yet Done)

### Priority 1: Fix Local Video Reconnect Issue 🐛

- **Symptom**: Local video works on first call, disappears on reconnect
- **Error**: "The play() request was interrupted by a new load request"
- **Likely cause**: Video track not being properly recreated or MediaStream being reused incorrectly
- **File to check**: `components/VideoAvatarClient.tsx` (useLocalVideo hook from @agora/conversational-ai)
- **Debug logs added**: Filter console for `📹 LOCAL_VIDEO_DEBUG` to track:
  - State changes (track creation/destruction)
  - Publish/unpublish lifecycle
  - handleStart, handleStop, toggleVideo actions

### Priority 2: Fix Chat Display 🐛

- **Symptom**: Only "Agent" label shows, message text hidden
- **File to check**: Chat/transcript component rendering in `components/VideoAvatarClient.tsx`
- **Possible cause**: CSS issue or text rendering logic broken
- **Component**: Uses `@agora/agent-ui-kit` Message/Response components (lines 314-344)

---

## Files Modified

1. `react-video-client-avatar/node_modules/@agora/conversational-ai/packages/conversational-ai/helper/rtc.ts`
   - Added video support to RTCHelper class

2. `react-video-client-avatar/hooks/useAgoraVideoClient.ts`
   - Switched from raw RTC client events to RTCHelper events
   - Simplified video handling

---

## Testing Notes

- Remote video (avatar): ✅ Working
- Remote audio: ✅ Working
- Local video (first call): ✅ Working
- Local video (reconnect): ✅ Working
- Chat display: ✅ Working

---

## Commands to Run

```bash
# Backend
cd /Users/benweekes/work/convoai/agent-samples/simple-backend
PORT=8082 python3 local_server.py

# Frontend
cd /Users/benweekes/work/convoai/agent-samples/react-video-client-avatar
npm run dev
```

---

## Important Notes

✅ **All fixes have been committed and pushed**

- Local video reconnect: Fixed in agent-toolkit (commit 5dd526a)
- Chat display: Fixed
- Video client: Refactored in agent-samples (commit 4f74ff3)

📝 **Package Management**

- RTCHelper changes are in agent-toolkit and published to GitHub
- Fresh `npm install` will pull latest fixes from `github:AgoraIO-Conversational-AI/agent-toolkit#main`

---

## Debugging Commands

```bash
# Filter for video debug logs in console
# Remote video (avatar): 🎥 VIDEO_DEBUG
# Local video: 📹 LOCAL_VIDEO_DEBUG

# Check for errors
# Look for: "play() request was interrupted"
```

## Debug Logs Added (2026-01-20)

### Local Video Reconnect Debugging

Added comprehensive logging in `components/VideoAvatarClient.tsx`:

1. **State tracking** (lines 95-102): Logs whenever local video state changes
   - `isLocalVideoActive` status
   - Track presence and ID
   - Connection status

2. **Publish lifecycle** (lines 108-114, 136-141): Logs publish/unpublish operations
   - Client availability
   - Track details
   - Success/failure states

3. **User actions** (lines 222-230, 250-268): Logs user-triggered events
   - handleStop flow (disable video → leave channel)
   - toggleVideo actions (enable/disable)
   - enableVideo during initial connection

**Usage:** Filter browser console for `📹 LOCAL_VIDEO_DEBUG` when testing reconnect scenario

---

### Chat Display Debugging

Added comprehensive logging to track message flow:

**In `hooks/useAgoraVideoClient.ts`:**

1. **Transcript updates** (lines 183-192, 210-214): Logs raw transcript events from RTM
   - Raw message count and content
   - Message UIDs, text, status
   - Text lengths
   - Completed vs in-progress separation

**In `components/VideoAvatarClient.tsx`:**

1. **Message list updates** (lines 54-65): Logs whenever messageList state changes
   - Message count
   - All messages with turn_id, uid, text, status
   - Agent vs user classification

2. **In-progress message updates** (lines 67-78): Logs current typing indicator
   - Whether in-progress message exists
   - Full message details if present

3. **Send message flow** (lines 236-242): Logs user message sending
   - Message content
   - Agent UID
   - Send success/failure

4. **Agent detection** (lines 273-274): Logs every isAgentMessage check
   - Input UID
   - Result (true/false)

**Usage:** Filter browser console for `💬 CHAT_DEBUG` to track message flow from RTM → state → render

---

## Production Deployment (EC2 + nginx on port 443)

This section documents how to serve all agent-samples behind nginx on port 443 alongside an existing application, using path-based routing.

### Architecture

```
nginx :443 (convoai-demo.agora.io)
  /                              → /var/www/palabra/         (existing SPA)
  /v1/, /query, /oauth, /pstn   → localhost:7080             (existing API)
  /simple-backend/               → localhost:8081             (Flask API, prefix stripped)
  /react-voice-client/           → localhost:8083             (Next.js voice client)
  /react-video-client-avatar/    → localhost:8084             (Next.js video+avatar client)
  /simple-voice-client-no-backend/     → static files via alias
  /simple-voice-client-with-backend/   → static files via alias
```

### Source Code Changes (4 lines, backward-compatible)

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
PORT=8081 exec python3 local_server.py
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
        proxy_pass http://localhost:8081/;
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

# Verify static assets load (not intercepted by palabra cache block)
curl -s -o /dev/null -w "%{http_code}" https://convoai-demo.agora.io/react-voice-client/_next/static/chunks/*.css
# 200
```

### Key Gotchas

1. **`^~` on proxy locations is required.** Without it, an existing `location ~* \.(js|css|...)$` regex block for static asset caching will intercept Next.js `_next/static/` requests and look for them in the wrong root directory, returning 404.

2. **PM2 Python interpreter bug.** PM2 (at least some versions) ignores the `interpreter` field for Python scripts and wraps them in its JS `ProcessContainerFork.js`, which Python then tries to parse as Python code. Workaround: use a bash shell script that activates the venv and runs Python directly.

3. **`NEXT_PUBLIC_*` env vars must be set at runtime too.** `next start` re-evaluates `next.config.ts` at startup. If `NEXT_PUBLIC_BASE_PATH` is only set during `npm run build` but not when `next start` runs (e.g., via PM2), basePath evaluates to `""` at runtime and all pages return 404 despite being correctly built.

4. **Trailing slash on `proxy_pass` for Flask.** `location /simple-backend/` paired with `proxy_pass http://localhost:8081/;` (note trailing `/`) strips the `/simple-backend/` prefix. Flask routes are `/start-agent`, not `/simple-backend/start-agent`.

5. **No changes needed for local dev.** When no `NEXT_PUBLIC_*` env vars are set, basePath defaults to `""` and backend URL defaults to `http://localhost:8082` — identical to the original behavior.
