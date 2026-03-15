# <img src="../assets/agora-logo.svg" alt="Agora" width="24" height="24" style="vertical-align: middle; margin-right: 8px;" /> React Voice AI Client

React/Next.js implementation demonstrating the Agora Conversational AI SDK and
UI Kit integration.

> **📘 For AI Coding Assistants:** See [../AGENT.md](../AGENT.md) for comprehensive implementation guidance and API reference.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Key Implementation Details](#key-implementation-details)
  - [Agent Visualizer](#agent-visualizer)
  - [Custom Hook: useAgoraVoiceClient](#custom-hook-useagoravoiceclient)
- [Message Types](#message-types)
- [Building for Production](#building-for-production)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Real-time Transcription** - Live transcription with turn deduplication and in-progress tracking
- **UI Components** - Domain-specific components from `@agora/agent-ui-kit` for voice AI
- **RTC Audio** - High-quality stereo audio with echo cancellation, noise suppression, and auto gain control
- **TypeScript** - Full type safety with Agora SDK and UI Kit types
- **React 19 & Next.js 16** - Latest React features and patterns

## Architecture

This sample application uses the Agora Conversational AI SDK and UI Kit packages installed from GitHub:

**Dependencies:**

- `agora-agent-client-toolkit` - Core SDK from [agent-client-toolkit-ts](https://github.com/AgoraIO-Conversational-AI/agent-client-toolkit-ts)
- `@agora/agent-ui-kit` - UI components from [agent-ui-kit](https://github.com/AgoraIO-Conversational-AI/agent-ui-kit)

**Key Components:**

1. **AgoraVoiceAI** - Main class managing RTC + RTM connections, transcript processing
2. **TranscriptHelper** - Turn deduplication, message assembly, in-progress tracking
3. **React hooks** - `useConversationalAI`, `useTranscript`, `useAgentState`
4. **UI Components** - Domain-specific components for chat, agent visualization, and settings

## Prerequisites

- Node.js >= 20.9.0 (required by Next.js 16)
- Python backend running on port 8082 (see `../simple-backend/`)

## Configuration

This client connects to the backend using the **VOICE profile** by default.

**Backend Configuration Required:**

The backend must be configured with `VOICE_*` prefixed environment variables. See [../simple-backend/.env.example](../simple-backend/.env.example) for the complete list of required credentials:

- VOICE_APP_ID, VOICE_APP_CERTIFICATE, VOICE_AGENT_AUTH_HEADER
- VOICE_LLM_API_KEY
- VOICE_TTS_VENDOR, VOICE_TTS_KEY, VOICE_TTS_VOICE_ID

This client runs on port **8083** and connects to the backend on port **8082**.

**Profile Override:**

You can override the default profile using the "Server Profile" field in the UI. Profile names are case-insensitive (VOICE, voice, or Voice all work).

## Setup and Run

**Install dependencies:**

```bash
npm install --legacy-peer-deps
```

The `--legacy-peer-deps` flag is required due to agora-rtm peer dependency requirements.

**Run development server:**

```bash
npm run dev
```

**Open browser:**

```
http://localhost:8083
```

## Usage

**Backend Configuration:**

The backend must be configured with AI agent credentials and settings. See
`../simple-backend/README.md` for configuration details.

**Start Services:**

1. **Start the Backend** (if not already running):

   ```bash
   cd ../simple-backend
   PORT=8082 python3 local_server.py
   ```

2. **Start the React Client**:

   ```bash
   npm run dev
   ```

3. **Connect to Agent**:
   - Backend URL should be `http://localhost:8082` (default)
   - Click "Start Conversation"
   - Client calls `/start-agent` endpoint on the backend

4. **Interact with Agent**:
   - Speak into your microphone
   - View real-time transcriptions in the chat window (bottom-right)
   - Toggle mute with the microphone button
   - End call with "End Call" button

## Project Structure

```
react-voice-client/
├── app/
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Main page with dynamic import
│   └── globals.css              # Tailwind CSS
├── components/
│   └── VoiceClient.tsx          # Main voice client component
├── hooks/
│   ├── use-audio-devices.ts
│   ├── use-is-mobile.ts
│   └── useAgoraVoiceClient.ts   # Custom hook for Agora integration
├── lib/
│   └── theme/                   # Theme utilities
├── icons/
│   └── PhoneReceiver.tsx        # Custom icons
├── package.json                 # Dependencies
└── README.md                    # This file
```

## Key Implementation Details

### Agent Visualizer

Shows Lottie animations for different agent states:

```typescript
<AgentVisualizer
  state={isAgentSpeaking ? "talking" : "listening"}
  size="lg"
/>
```

**Available States:**

- `not-joined` - Not connected
- `joining` - Connecting to channel
- `ambient` - Connected but idle
- `listening` - Listening to user
- `analyzing` - Processing user input
- `talking` - Agent is speaking
- `disconnected` - Disconnected from channel

### Custom Hook: useAgoraVoiceClient

Encapsulates all Agora RTC logic:

```typescript
const {
  isConnected,
  isMuted,
  micState,
  messageList,
  currentInProgressMessage,
  isAgentSpeaking,
  joinChannel,
  leaveChannel,
  toggleMute,
} = useAgoraVoiceClient();
```

**Responsibilities:**

- AgoraVoiceAI lifecycle management (connect/disconnect)
- Transcript state via toolkit hooks
- Microphone track creation with AEC/ANS/AGC
- Agent speaking state detection
- Mute/unmute and text messaging

## Message Types

The MessageEngine processes these message types from RTC stream-message events:

### User Transcription

```typescript
{
  object: "user.transcription",
  text: "Hello, how are you?",
  final: true,
  turn_id: 123,
  stream_id: 1234,
  user_id: "1234",
  language: "en-US",
  start_ms: 0,
  duration_ms: 1500,
  words: [
    { word: "Hello", start_ms: 0, duration_ms: 200, stable: true },
    { word: "how", start_ms: 200, duration_ms: 150, stable: true },
    ...
  ]
}
```

### Agent Transcription

```typescript
{
  object: "assistant.transcription",
  text: "I'm doing well, thank you!",
  quiet: false,
  turn_seq_id: 1,
  turn_status: 1,  // 0=IN_PROGRESS, 1=END, 2=INTERRUPTED
  turn_id: 124,
  stream_id: 0,
  user_id: "0",
  language: "en-US",
  start_ms: 0,
  duration_ms: 2000,
  words: [...]
}
```

### Message Interrupt

```typescript
{
  object: "message.interrupt",
  message_id: "msg_123",
  data_type: "message",
  turn_id: 124,
  start_ms: 1500,
  send_ts: 1234567890
}
```

## Building for Production

```bash
npm run build
npm start
```

The build creates an optimized production bundle with:

- Server-side rendering disabled for browser-only components (Agora SDK)
- TypeScript type checking
- Optimized static pages

## Tech Stack

- **Framework**: Next.js 16 with App Router and Turbopack
- **Language**: TypeScript 5
- **Runtime**: React 19
- **Styling**: Tailwind CSS v4
- **UI Components**: @agora/agent-ui-kit
- **RTC SDK**: agora-rtc-sdk-ng v4.24+
- **Icons**: lucide-react
- **Animations**: @lottiefiles/dotlottie-react

## Contributing

When adding new features:

1. Use existing @agora/agent-ui-kit components when possible
2. Keep imports using `@/` alias for consistency
3. Update TypeScript types appropriately
4. Test build with `npm run build` before committing
5. Update this README if adding new major features

## License

MIT
