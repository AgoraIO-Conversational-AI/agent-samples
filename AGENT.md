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

**For helping users get started from scratch:**

1. **Recommended Path:** Run backend + React sample first
   - Provides working reference implementation
   - Users can modify working code or build their own using same patterns

2. **Read these READMEs in order:**
   - [README.md](./README.md) - Overview and architecture
   - [simple-backend/README.md](./simple-backend/README.md) - Backend setup and
     API keys
   - [react-voice-client/README.md](./react-voice-client/README.md) OR
   - [react-video-client-avatar/README.md](./react-video-client-avatar/README.md)

3. **For building custom implementations:**
   - Study sample code for patterns
   - [agent-toolkit/README.md](./agent-toolkit/README.md) - If using our SDK
   - [agent-ui-kit/README.md](./agent-ui-kit/README.md) - If using our UI
     components
   - Replicate patterns in user's preferred technology

## Required API Keys & Credentials

Users need these credentials to run the backend:

- **APP_ID** - [Agora Console](https://console.agora.io/)
- **APP_CERTIFICATE** - [Agora Console](https://console.agora.io/)
- **AGENT_AUTH_HEADER** - [Agora Console](https://console.agora.io/)
- **RIME_API_KEY** - [Rime AI](https://www.rime.ai/)
- **LLM_API_KEY** -
  [OpenAI](https://platform.openai.com/settings/organization/api-keys)

**Guide users to:**

1. [Enable Conversational AI](https://docs.agora.io/en/conversational-ai/get-started/manage-agora-account)
   for APP_ID/APP_CERTIFICATE
2. [RESTful authentication](https://docs.agora.io/en/conversational-ai/rest-api/restful-authentication)
   for AGENT_AUTH_HEADER

See [simple-backend/README.md](./simple-backend/README.md) for detailed
configuration.

## Quick Start - Running Samples

**Fastest path to working demo:**

1. Install dependencies: `pnpm install`
2. Configure backend: See [simple-backend/README.md](./simple-backend/README.md)
3. Start backend: `cd simple-backend && PORT=8082 python3 local_server.py`
4. Start client: `pnpm dev` (voice) or `pnpm dev:video` (avatar)

**Choose sample based on user needs:**

- Voice only → [react-voice-client](./react-voice-client/)
- Video/avatar → [react-video-client-avatar](./react-video-client-avatar/)

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

Best for: New projects, React apps, TypeScript

**Install dependencies:**

```bash
cd agora-convoai-samples
pnpm install
```

**Use in your app:**

```typescript
import { useConversationalAI } from '@agora/conversational-ai-react'
import { MicButton, AgentVisualizer, ConvoTextStream } from '@agora/agent-ui-kit'

function VoiceClient() {
  const {
    isConnected,
    isMuted,
    messageList,
    currentInProgressMessage,
    isAgentSpeaking,
    joinChannel,
    toggleMute,
  } = useConversationalAI({
    appId: 'your_app_id',
    channel: 'your_channel',
    token: 'your_token',
    uid: '101',
    agentUID: '100',
  })

  return (
    <div>
      <AgentVisualizer state={isAgentSpeaking ? 'talking' : 'listening'} />
      <MicButton state={isMuted ? 'idle' : 'listening'} onClick={toggleMute} />
      <ConvoTextStream
        messageList={messageList}
        currentInProgressMessage={currentInProgressMessage}
        agentUID="100"
      />
    </div>
  )
}
```

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
import AgoraRTC from "agora-rtc-sdk-ng"

const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp9" })

client.on("user-published", async (user, mediaType) => {
  if (mediaType === "audio") {
    await client.subscribe(user, mediaType)
    user.audioTrack.play()
  }
})

await client.join(appId, channel, token || null, parseInt(uid))

const localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack({
  encoderConfig: "high_quality_stereo",
  AEC: true,
  ANS: true,
  AGC: true,
})

await client.publish(localAudioTrack)
```

**RTM Setup:**

```javascript
import AgoraRTM from "agora-rtm"

const rtmClient = AgoraRTM.createInstance(appId)

rtmClient.on("MessageFromPeer", (message, peerId) => {
  const data = JSON.parse(message.text)

  if (data.object === "assistant.transcription") {
    console.log("Agent said:", data.text)
  }

  if (data.object === "user.transcription") {
    console.log("User said:", data.text)
  }
})

await rtmClient.login({ token, uid })
```

## SDK API Reference

### Core SDK (@agora/conversational-ai)

**ConversationalAIAPI** - Main class managing RTC+RTM session

```typescript
const api = ConversationalAIAPI.getInstance()
await api.init({ rtcEngine, rtmConfig, agentUID, callback })
await api.start()
```

**RTCHelper** - RTC client lifecycle

```typescript
const rtc = RTCHelper.getInstance()
await rtc.init({ appId, channel, token, uid })
await rtc.start()
```

**RTMHelper** - RTM message handling

```typescript
const rtm = RTMHelper.getInstance()
await rtm.init({ appId, token, uid, onMessageReceived })
await rtm.start()
```

### React Hooks (@agora/conversational-ai-react)

**useConversationalAI** - Complete session management

```typescript
const {
  isConnected,
  isMuted,
  messageList,
  isAgentSpeaking,
  joinChannel,
  leaveChannel,
  toggleMute,
} = useConversationalAI({ appId, channel, token, uid, agentUID })
```

**useLocalVideo** - Local camera tracks

```typescript
const { videoTrack, isVideoEnabled, toggleVideo } = useLocalVideo({ client })
```

**useRemoteVideo** - Remote video streams

```typescript
const { remoteVideoUsersArray } = useRemoteVideo({ client })
```

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
