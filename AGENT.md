# Agora Conversational AI - AI Coding Assistant Guide

Guide for AI coding assistants to help developers integrate Agora Conversational
AI voice and video agents.

## Purpose

This guide helps AI coding assistants help developers:

1. **Run the sample applications** (backend + React client)
2. **Understand the reference implementations** to replicate functionality
3. **Integrate Agora Conversational AI** into their own applications

**Key Principle:** The samples are production-quality reference implementations.
Use them as templates for implementing similar functionality in any client or
server technology.

## Table of Contents

- [Getting Started](#getting-started---first-steps)
- [Required API Keys](#required-api-keys--credentials)
- [Quick Start](#quick-start---running-samples)
- [Using Samples as Reference](#using-the-samples-as-reference)
- [Architecture Overview](#architecture)
- [Implementation Approaches](#implementation-approaches)
- [SDK API Reference](#sdk-api-reference)
- [UI Kit Components](#ui-kit-components)
- [Backend Setup](#backend-setup)
- [Common Issues](#common-issues)
- [Common Implementation Tasks](#common-implementation-tasks)
- [Documentation Index](#documentation-index)

## Getting Started - First Steps

**AI Assistant: Follow this process when user wants to run samples:**

1. **Choose React sample** (unless user explicitly asks for basic HTML/JS)
   - Voice only: `react-voice-client` (default choice)
   - Video/avatar: `react-video-client-avatar`
   - Basic samples: Only if user specifically requests vanilla JS/HTML

2. **Install and build FIRST** - Do this before asking for credentials
   - Backend: `cd simple-backend && pip install -r requirements.txt`
   - Client: `cd react-voice-client && npm install --legacy-peer-deps`
   - Verify builds complete successfully

3. **Then gather credentials interactively** - Do NOT just list requirements
   - Ask for each credential one by one (see example interaction below)
   - Provide console links for each credential
   - Create `.env` file in `simple-backend/` with provided values
   - Explain what each credential is for

4. **Start services**
   - Backend: `cd simple-backend && PORT=8082 python3 local_server.py`
   - Client: `cd react-voice-client && npm run dev`
   - Provide the local URL to access the client

**Be proactive - start building immediately, don't ask which client to use first.**

---

**For building custom implementations:**

- Study sample code for patterns
- [agent-toolkit/README.md](./agent-toolkit/README.md) - If using our SDK
- [agent-ui-kit/README.md](./agent-ui-kit/README.md) - If using our UI components
- Replicate patterns in user's preferred technology

## Required API Keys & Credentials

**AI Assistant Instructions: Helping Users Get Credentials**

When helping users get started, you should:

1. **Request credentials interactively** instead of just listing requirements
2. **Offer to create the `.env` file** with the provided values
3. **Provide direct links** to get each credential (see below)
4. **Validate configuration** before running the backend
5. **Explain each credential** and why it's needed

**Example interaction for Voice Agent:**

```
AI: I'll set up the Voice AI Agent. Please provide all required credentials:

**Agora Credentials:**
1. APP_ID - Console: https://console.agora.io/project-management
   Help: https://docs.agora.io/en/conversational-ai/get-started/manage-agora-account
2. AGENT_AUTH_HEADER - Console: https://console.agora.io/restful-api
   Help: https://docs.agora.io/en/conversational-ai/rest-api/restful-authentication
3. APP_CERTIFICATE (optional for testing) - Same project page

**LLM & TTS:**
4. LLM_API_KEY - https://platform.openai.com/settings/organization/api-keys
5. TTS_VENDOR - Choose: rime, elevenlabs, openai, or cartesia
6. TTS_KEY - Get from your chosen vendor:
   Rime: https://rime.ai/ | ElevenLabs: https://elevenlabs.io/
   OpenAI: https://platform.openai.com/ | Cartesia: https://cartesia.ai/
7. TTS_VOICE_ID - Voice ID for your chosen vendor

[User provides all values in one response]
[AI creates .env file in simple-backend/ and proceeds with installation]
```

**Example interaction for Video Agent:**

```
AI: I'll set up the Video AI Agent with avatar. Please provide all required credentials:

**Agora Credentials:**
1. APP_ID - Console: https://console.agora.io/project-management
2. AGENT_AUTH_HEADER - Console: https://console.agora.io/restful-api
3. APP_CERTIFICATE (optional) - Same project page

**LLM & TTS:**
4. LLM_API_KEY - https://platform.openai.com/settings/organization/api-keys
5. TTS_VENDOR - Choose: rime, elevenlabs, openai, or cartesia
6. TTS_KEY - Get from chosen vendor (Rime | ElevenLabs | OpenAI | Cartesia)
7. TTS_VOICE_ID - Voice ID for chosen vendor

**Avatar Settings (AVATAR_ prefix):**
8. AVATAR_AVATAR_VENDOR - Choose: heygen or anam
   HeyGen: https://www.heygen.com/ | Anam AI: https://www.anam.ai/
9. AVATAR_AVATAR_API_KEY - API key from avatar provider
10. AVATAR_AVATAR_ID - Avatar identifier from provider

Optional (for different avatar config):
- AVATAR_APP_ID - Different Agora app (e.g., beta instance)
- AVATAR_APP_CERTIFICATE - Certificate for avatar app
- AVATAR_AGENT_AUTH_HEADER - Auth header for avatar app
- AVATAR_LLM_API_KEY - Different LLM key
- AVATAR_TTS_VENDOR, AVATAR_TTS_KEY, AVATAR_TTS_VOICE_ID - Different TTS

[User provides all values in one response]
[AI creates .env file with both base and AVATAR_ credentials]
```

**Base Requirements (Voice Clients):**

- **APP_ID** - [Agora Console → Project Management](https://console.agora.io/project-management)
  - Help: [Manage Agora Account](https://docs.agora.io/en/conversational-ai/get-started/manage-agora-account)
- **APP_CERTIFICATE** - [Agora Console → Project Management](https://console.agora.io/project-management) (optional for testing)
- **AGENT_AUTH_HEADER** - [Agora Console → RESTful API](https://console.agora.io/restful-api)
  - Help: [RESTful Authentication](https://docs.agora.io/en/conversational-ai/rest-api/restful-authentication)
- **LLM_API_KEY** - [OpenAI API Keys](https://platform.openai.com/settings/organization/api-keys)
- **TTS_VENDOR** - Choose TTS provider: `rime`, `elevenlabs`, `openai`, or `cartesia`
- **TTS_KEY** - API key for your chosen TTS provider
  - [Rime](https://rime.ai/) | [ElevenLabs](https://elevenlabs.io/) | [OpenAI](https://platform.openai.com/) | [Cartesia](https://cartesia.ai/)
- **TTS_VOICE_ID** - Voice/speaker ID for your chosen TTS provider

**Additional Requirements for Avatar Video Client:**

Use profile-based configuration to run avatar clients with completely different credentials:

- **AVATAR_APP_ID** - Different Agora app (e.g., for beta instance)
- **AVATAR_APP_CERTIFICATE** - Certificate for avatar app
- **AVATAR_AGENT_AUTH_HEADER** - Auth header for avatar app
- **AVATAR_LLM_API_KEY** - Different LLM API key
- **AVATAR_TTS_VENDOR** - Different TTS vendor (e.g., elevenlabs)
- **AVATAR_TTS_KEY** - Different TTS API key
- **AVATAR_TTS_VOICE_ID** - Different voice
- **AVATAR_AVATAR_VENDOR** - Avatar provider: `heygen` or `anam`
- **AVATAR_AVATAR_API_KEY** - Avatar provider API key
  - [HeyGen](https://www.heygen.com/) | [Anam AI](https://www.anam.ai/)
- **AVATAR_AVATAR_ID** - Avatar identifier from provider

See [simple-backend/README.md](./simple-backend/README.md) for detailed configuration examples.

## Integrating into Your App

**Decision tree for existing applications:**

- **Have existing React/Next.js app?** → Use [Approach A: SDK Packages](#approach-a-sdk-packages-recommended)
  - Install `@agora/conversational-ai-react` and `@agora/agent-ui-kit`
  - Import hooks and components into your existing app
  - Best for: Adding voice AI to existing React projects

- **Have existing Vue/Angular/vanilla JS app?** → Use [Approach C: Bare RTC/RTM](#approach-c-bare-rtcrtm)
  - Install `agora-rtc-sdk-ng` and `agora-rtm` directly
  - Implement connection patterns from samples
  - Best for: Non-React frameworks, mobile apps

- **Starting from scratch?** → Use [Approach B: Sample as Template](#approach-b-sample-as-template)
  - Copy `react-voice-client` or `react-video-client-avatar`
  - Customize UI and functionality
  - Best for: New projects, rapid prototyping

- **Need custom backend (Node.js/Go/Java)?** → Study [simple-backend/](./simple-backend/)
  - Reference token generation patterns
  - Reference Agent REST API calls
  - Replicate in your preferred language

## Using the Samples as Reference

**The samples demonstrate production patterns you can replicate:**

**Backend Reference ([simple-backend/](./simple-backend/)):**

- Token generation (v007 with RTC+RTM)
- Agent REST API calls (start/stop agents)
- Profile-based configuration
- Environment variable management
- Can be replicated in Node.js, Go, Java, PHP, etc.

**Client Reference ([react-voice-client/](./react-voice-client/),
[react-video-client-avatar/](./react-video-client-avatar/)):**

- RTC/RTM connection management
- Agent communication patterns
- Real-time transcription handling
- UI state management
- Can be replicated in Vue, Angular, vanilla JS, mobile apps, etc.

**When helping users build their own implementations:**

1. **Read the relevant sample code** to understand the pattern
2. **Adapt the pattern** to user's technology stack
3. **Reference specific files** (e.g., "See simple-backend/core/agent.py:45 for
   agent creation")
4. **Maintain the same architecture** (backend generates tokens, calls Agent
   API; client joins channel via RTC/RTM)

## Architecture

### System Overview

```
                          ┌─────────────────────────┐
                          │  Your Backend Services  │
                          └───────┬───────────┬─────┘
                                 ╱             ╲
                                ╱               ╲
                               ╱                 ╲
                              ╱                   ╲
         1. Serves client app│                     │3. Agent REST API
         2. Provides token,  │                     │   (token, uid, channel,
            uid, channel     │                     │    agent properties)
                            ╱                       ╲
                           ╱                         ╲
                          ↓                           ↓
              ┌────────────────────┐      ┌────────────────────┐
              │  Voice AI Client   │      │  AI Agent Instance │
              └──────────┬─────────┘      └─────────┬──────────┘
                         │                          │
                         │     ┌──────────────┐     │
                         └────→│ Agora SD-RTN │←────┘
                               │ Audio, Video,│
                               │     Data     │
                               └──────────────┘
```

**Flow:**

1. Backend serves client app and generates credentials (token, uid, channel)
2. Backend calls Agora Agent REST API to start AI agent
3. Both client and agent join same Agora channel
4. Real-time audio/video/data flows through SD-RTN

### Repository Structure

```
agora-convoai-samples/
├── agent-toolkit/                 # SDK Implementation
│   ├── conversational-ai-api/     # Core SDK
│   │   ├── helper/                # RTC and RTM helpers
│   │   ├── utils/                 # Utilities
│   │   └── index.ts              # Main exports
│   └── react/                     # React hooks
│       └── use-conversational-ai.ts
│
├── agent-ui-kit/                  # UI Components
│   ├── components/
│   │   ├── voice/                # Voice components
│   │   ├── chat/                 # Chat components
│   │   ├── video/                # Video components
│   │   └── layout/               # Layout helpers
│   └── index.ts
│
├── react-voice-client/            # Voice sample app
├── react-video-client-avatar/     # Video sample app
├── simple-voice-client/           # HTML/JS sample
└── simple-backend/                # Python backend
```

### RTC and RTM Explained

**RTC (Real-Time Communication)**

- Audio and video streaming between client and agent
- Low-latency transport with echo cancellation, noise suppression
- Used for: Voice input/output, video streams, audio visualizations

**RTM (Real-Time Messaging)**

- Text messages and control signals
- Live transcriptions, turn status, interrupts
- Used for: Chat display, agent state, structured JSON messages

Both use the same channel and require proper token generation.

## Implementation Approaches

### Approach A: SDK Packages (Recommended)

Best for: React apps adding voice AI to existing projects

**Install dependencies:**

```bash
npm install agora-rtc-sdk-ng agora-rtm
npm install @agora/agent-ui-kit  # Optional: Pre-built UI components
```

**Implementation pattern:**

Study `react-voice-client/hooks/useAgoraVoiceClient.ts` for the complete pattern. The core approach:

```typescript
import AgoraRTC from 'agora-rtc-sdk-ng'
import AgoraRTM from 'agora-rtm'
import { MicButton, AgentVisualizer, ConvoTextStream } from '@agora/agent-ui-kit'

function VoiceClient() {
  // 1. Initialize RTC client
  const rtcClient = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp9' })

  // 2. Initialize RTM client for transcriptions
  const rtmClient = AgoraRTM.createInstance(appId)

  // 3. Handle RTM messages for transcriptions
  rtmClient.on('MessageFromPeer', (message) => {
    const data = JSON.parse(message.text)
    // Handle user.transcription and assistant.transcription
  })

  // 4. Use UI Kit components
  return (
    <div>
      <AgentVisualizer state={isAgentSpeaking ? 'talking' : 'listening'} />
      <MicButton state={isMuted ? 'idle' : 'listening'} onClick={toggleMute} />
      <ConvoTextStream messageList={messageList} agentUID="100" />
    </div>
  )
}
```

See `react-voice-client/` for complete reference implementation.

### Approach B: Sample as Template

Best for: Quick prototyping, learning by example

**Voice only:**

```bash
cp -r react-voice-client my-voice-app
cd my-voice-app
pnpm install
pnpm dev
```

**Video + Avatar:**

```bash
cp -r react-video-client-avatar my-video-app
cd my-video-app
pnpm install
pnpm dev
```

### Approach C: Bare RTC/RTM

Best for: Non-React apps, custom integrations

```bash
npm install agora-rtc-sdk-ng agora-rtm
```

**RTC Setup:**

```javascript
import AgoraRTC from "agora-rtc-sdk-ng";

const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp9" });

client.on("user-published", async (user, mediaType) => {
  if (mediaType === "audio") {
    await client.subscribe(user, mediaType);
    user.audioTrack.play();
  }
});

await client.join(appId, channel, token || null, parseInt(uid));

const localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack({
  encoderConfig: "high_quality_stereo",
  AEC: true,
  ANS: true,
  AGC: true,
});

await client.publish(localAudioTrack);
```

**RTM Setup:**

```javascript
import AgoraRTM from "agora-rtm";

const rtmClient = AgoraRTM.createInstance(appId);

rtmClient.on("MessageFromPeer", (message, peerId) => {
  const data = JSON.parse(message.text);

  if (data.object === "assistant.transcription") {
    console.log("Agent said:", data.text);
  }

  if (data.object === "user.transcription") {
    console.log("User said:", data.text);
  }
});

await rtmClient.login({ token, uid });
```

## SDK API Reference

### Agora RTC SDK (agora-rtc-sdk-ng)

**Core RTC client:**

```typescript
import AgoraRTC from "agora-rtc-sdk-ng";

const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp9" });
await client.join(appId, channel, token || null, parseInt(uid));

const localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack({
  encoderConfig: "high_quality_stereo",
  AEC: true, // Echo cancellation
  ANS: true, // Noise suppression
  AGC: true, // Auto gain control
});

await client.publish(localAudioTrack);
```

### Agora RTM SDK (agora-rtm)

**Message handling:**

```typescript
import AgoraRTM from "agora-rtm";

const rtmClient = AgoraRTM.createInstance(appId);

rtmClient.on("MessageFromPeer", (message, peerId) => {
  const data = JSON.parse(message.text);
  if (data.object === "assistant.transcription") {
    // Handle agent transcription
  }
  if (data.object === "user.transcription") {
    // Handle user transcription
  }
});

await rtmClient.login({ token, uid });
```

### React Hooks (@agora/conversational-ai)

**useLocalVideo** - Local camera tracks

```typescript
import { useLocalVideo } from "@agora/conversational-ai";

const { videoTrack, isVideoEnabled, toggleVideo } = useLocalVideo();
```

**useRemoteVideo** - Remote video streams

```typescript
import { useRemoteVideo } from "@agora/conversational-ai";

const { remoteVideoUsersArray } = useRemoteVideo({ client });
```

**Custom hook pattern:**

For complete voice AI integration, reference `react-voice-client/hooks/useAgoraVoiceClient.ts`

## UI Kit Components

### Voice Components

| Component         | Purpose                                                             |
| ----------------- | ------------------------------------------------------------------- |
| `MicButton`       | Microphone control with states (idle, listening, processing, error) |
| `AgentVisualizer` | Animated agent visual (listening, talking, analyzing, ambient)      |
| `AudioVisualizer` | Real-time audio level visualization                                 |
| `MicSelector`     | Microphone device selection dropdown                                |

### Chat Components

| Component         | Purpose                                         |
| ----------------- | ----------------------------------------------- |
| `Conversation`    | Chat container with scroll management           |
| `Message`         | Message bubble (user/assistant roles)           |
| `ConvoTextStream` | Auto-updating transcript display with streaming |

### Video Components

| Component            | Purpose                                    |
| -------------------- | ------------------------------------------ |
| `LocalVideoPreview`  | Local camera preview with mirror effect    |
| `AvatarVideoDisplay` | Remote avatar video with connection states |
| `Avatar`             | Profile avatar image                       |

### Layout Components

| Component    | Purpose                           |
| ------------ | --------------------------------- |
| `VideoGrid`  | Desktop 2x2 grid layout for video |
| `MobileTabs` | Mobile tab switcher (Video/Chat)  |

## Backend Setup

### Token Generation (v007 with RTC+RTM)

```python
from agora_token_builder import AccessToken, ServiceRtc, ServiceRtm

def build_token_with_rtm(channel, uid, app_id, app_certificate):
    if not app_certificate:
        return ""

    token = AccessToken(app_id, app_certificate)

    # RTC Service
    rtc_service = ServiceRtc(channel, uid)
    rtc_service.add_privilege(ServiceRtc.kPrivilegeJoinChannel, 3600)
    rtc_service.add_privilege(ServiceRtc.kPrivilegePublishAudioStream, 3600)
    token.add_service(rtc_service)

    # RTM Service
    rtm_service = ServiceRtm(uid)
    rtm_service.add_privilege(ServiceRtm.kPrivilegeLogin, 3600)
    token.add_service(rtm_service)

    return token.build()
```

### Start Agent Endpoint

```python
@app.route('/start-agent', methods=['GET'])
def start_agent():
    channel = request.args.get('channel', f'ch_{int(time.time())}')

    # Generate token with RTC+RTM
    user_token = build_token_with_rtm(channel, "101", APP_ID, APP_CERTIFICATE)

    # Start agent via REST API
    agent_response = start_agent(
        channel=channel,
        app_id=APP_ID,
        agent_auth_header=AGENT_AUTH_HEADER,
        llm_config={...},
        tts_config={...},
        asr_config={...}
    )

    return jsonify({
        "appid": APP_ID,
        "token": user_token,
        "uid": "101",
        "channel": channel,
        "agent_response": agent_response
    })
```

### Agent Configuration

```python
# Agent REST API endpoint
url = f"https://api.agora.io/api/conversational-ai-agent/v2/projects/{app_id}/join"

payload = {
    "name": channel,
    "properties": {
        "channel": channel,
        "token": token,
        "agent_rtc_uid": "100",
        "agent_rtm_uid": f"100-{channel}",
        "remote_rtc_uids": ["*"],  # Use specific UID for avatar mode
        "enable_string_uid": False,
        "advanced_features": {
            "enable_bhvs": True,
            "enable_rtm": True,
            "enable_aivad": False
        },
        "idle_timeout": 120,
        "llm": {...},
        "tts": {...},
        "asr": {...}
    }
}
```

### Profile-Based Configuration

Override configuration per use case using profile-specific environment
variables:

```bash
# .env file
AVATAR_APP_ID=your_beta_app_id
AVATAR_TTS_VENDOR=elevenlabs
AVATAR_TTS_KEY=sk_your_key
AVATAR_TTS_VOICE_ID=cgSgspJ2msm6clMCkdW9
AVATAR_AVATAR_ENABLED=true
AVATAR_AVATAR_VENDOR=anam
```

**Usage:**

```bash
curl "http://localhost:8081/start-agent?channel=test&profile=avatar"
```

**Variable Precedence:**

1. `AVATAR_TTS_VENDOR` (profile-specific)
2. `TTS_VENDOR` (base variable)
3. Default value (hardcoded)

See [simple-backend/README.md](./simple-backend/README.md#profile-support) for
details.

### TTS Configuration

All TTS vendors use the same three environment variables:

```bash
TTS_VENDOR=  # Required: rime, elevenlabs, openai, or cartesia
TTS_KEY=     # Required: API key for your TTS vendor
TTS_VOICE_ID=  # Required: Voice/speaker ID for your chosen vendor
```

**Voice ID examples by vendor:**

- **Rime**: `astra`, `deedee`, `marsh`
- **ElevenLabs**: Get from [voice library](https://elevenlabs.io/)
- **OpenAI**: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Cartesia**: Get from [voice library](https://cartesia.ai/)

**Profile-specific TTS example:**

Use different TTS vendors per profile (e.g., Rime for voice, ElevenLabs for avatar):

```bash
# Base (voice clients)
TTS_VENDOR=rime
TTS_KEY=rime_api_key
TTS_VOICE_ID=astra

# Avatar profile
AVATAR_TTS_VENDOR=elevenlabs
AVATAR_TTS_KEY=elevenlabs_key
AVATAR_TTS_VOICE_ID=voice_id_here
```

### Avatar Configuration

When using video avatar clients, configure avatar-specific settings:

```bash
AVATAR_AVATAR_VENDOR=heygen  # or anam
AVATAR_AVATAR_API_KEY=your_avatar_api_key
AVATAR_AVATAR_ID=your_avatar_id
```

The client sends `?profile=avatar` to use these settings automatically.

See [simple-backend/README.md#avatar-mode-profile-example](./simple-backend/README.md#avatar-mode-profile-example) for complete examples.

## Installation & Setup

### First Time Setup

1. **Install pnpm:**

   ```bash
   npm install -g pnpm
   ```

2. **Install workspace dependencies:**

   ```bash
   pnpm install
   ```

3. **Install backend dependencies:**

   ```bash
   cd simple-backend
   pip install -r requirements-local.txt
   ```

4. **Configure backend:**

   ```bash
   cp simple-backend/.env.example simple-backend/.env
   # Edit .env with your credentials
   ```

### Running Services

**Start backend:**

```bash
cd simple-backend
PORT=8082 python3 local_server.py
```

**Start frontend:**

```bash
pnpm dev
```

**Access:**

- Frontend: http://localhost:8083
- Backend: http://localhost:8082

## Common Issues

**"UID_CONFLICT" error**

- Multiple clients using same UID
- Ensure cleanup before rejoin: `await client.leave()`

**"no such stream id" error**

- Agent UID mismatch between backend config and client subscription
- Verify `agentUID` matches `agent_rtc_uid` in backend

**Token errors**

- Pass `null` not empty string when no certificate: `token || null`
- Use `parseInt(uid)` for RTC client join

**Agent not speaking**

- Check TTS vendor API key in backend `.env`
- Verify backend logs for agent creation errors

**Can't hear user**

- Check microphone permissions in browser
- Verify audio track creation with AEC/ANS/AGC enabled

**Video not showing (avatar mode)**

- Ensure backend uses specific UID for `remote_rtc_uids`, not wildcard `"*"`
- Check `useMediaStream={true}` prop for multi-instance video rendering
- Verify avatar endpoint configured correctly

**Module not found**

- Run `pnpm install` from repository root
- Check workspace packages linked correctly

## Workspace Architecture

This project uses **pnpm workspace monorepo** where SDK and UI Kit are proper
packages:

**Benefits:**

- Single source of truth - update once, reflects everywhere
- Proper package development - can be published to npm
- External consumption - apps outside repo can use published packages
- Dependency hoisting - pnpm correctly resolves peer dependencies

**Package linking:**

```json
{
  "dependencies": {
    "@agora/conversational-ai": "workspace:*",
    "@agora/conversational-ai-react": "workspace:*",
    "@agora/agent-ui-kit": "workspace:*"
  }
}
```

## Common Implementation Tasks

**Task: Help user build Node.js backend**

1. Read [simple-backend/README.md](./simple-backend/README.md)
2. Reference `simple-backend/core/tokens.py` for token generation pattern
3. Reference `simple-backend/core/agent.py` for Agent REST API pattern
4. Adapt Python patterns to Node.js (Express, environment variables, etc.)

**Task: Help user build Vue.js client**

1. Read [react-voice-client/README.md](./react-voice-client/README.md)
2. Reference `react-voice-client/hooks/useAgoraVoiceClient.ts` for connection
   patterns
3. Study RTC/RTM setup in "Approach C: Bare RTC/RTM" section above
4. Adapt React patterns to Vue composition API

**Task: Help user add avatar to existing app**

1. Read
   [react-video-client-avatar/README.md](./react-video-client-avatar/README.md)
2. Reference `react-video-client-avatar/components/VideoAvatarClient.tsx`
3. Note: Client passes `profile=avatar` to backend
4. Backend uses profile-specific config (see Backend README Profile Support
   section)

**Task: Help user understand transcription messages**

1. See "Message Types" section above
2. Reference `agent-toolkit/conversational-ai-api/helper/rtm.ts` for RTM message
   handling
3. Study how react-voice-client displays transcriptions

## Documentation Index

**Core Documentation (Read these first):**

- [README.md](./README.md) - Repository overview, system architecture
- [simple-backend/README.md](./simple-backend/README.md) - Backend reference
  implementation
- [react-voice-client/README.md](./react-voice-client/README.md) - Voice client
  reference
- [react-video-client-avatar/README.md](./react-video-client-avatar/README.md) -
  Video client reference

**SDK & Components (For using our packages):**

- [agent-toolkit/README.md](./agent-toolkit/README.md) - Core SDK and React
  hooks API
- [agent-ui-kit/README.md](./agent-ui-kit/README.md) - React UI component
  library

**When to read each:**

| User Need                           | Read This                | Use Pattern From            |
| ----------------------------------- | ------------------------ | --------------------------- |
| Run samples quickly                 | Backend + Client README  | N/A - just run it           |
| Build backend in Python             | Backend README           | simple-backend/ code        |
| Build backend in Node/Go/etc        | Backend README           | simple-backend/ patterns    |
| Build React client                  | Client + agent-toolkit   | react-voice-client/ code    |
| Build Vue/Angular/vanilla JS client | Client + RTC/RTM section | react-voice-client/patterns |
| Use our React SDK                   | agent-toolkit README     | Import from packages        |
| Use our UI components               | agent-ui-kit README      | Import from packages        |
| Build custom UI                     | agent-ui-kit README      | See patterns, build own     |

**Key File References:**

**Backend Implementation:**

- `simple-backend/core/agent.py` - Agent REST API calls
- `simple-backend/core/tokens.py` - Token generation (v007)
- `simple-backend/core/config.py` - Environment variable handling
- `simple-backend/local_server.py` - Flask server example

**Client Implementation:**

- `react-voice-client/hooks/useAgoraVoiceClient.ts` - RTC/RTM connection
  management
- `react-voice-client/components/VoiceClient.tsx` - Complete voice client
- `react-video-client-avatar/components/VideoAvatarClient.tsx` - Complete video
  client
- `agent-toolkit/conversational-ai-api/helper/rtc.ts` - RTC helper patterns
- `agent-toolkit/conversational-ai-api/helper/rtm.ts` - RTM helper patterns
