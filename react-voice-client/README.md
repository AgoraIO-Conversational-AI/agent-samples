# <img src="../assets/agora-logo.svg" alt="Agora" width="24" height="24" style="vertical-align: middle; margin-right: 8px;" /> React Voice AI Client

React/Next.js implementation demonstrating the Agora Conversational AI SDK and
UI Kit integration.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Key Implementation Details](#key-implementation-details)
  - [MessageEngine Integration](#messageengine-integration)
  - [ConvoTextStream Component](#convotextstream-component)
  - [Agent Visualizer](#agent-visualizer)
  - [Microphone Button](#microphone-button)
  - [Custom Hook: useAgoraVoiceClient](#custom-hook-useagoravoiceclient)
- [Message Types](#message-types)
- [Building for Production](#building-for-production)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Workspace Architecture** - Uses pnpm workspace packages for SDK and UI Kit
- **Real-time Transcription** - Live transcription rendering with word-level and
  text-level modes
- **UI Components** - Pre-built components for chat, audio visualization, and
  agent state
- **MicButton** - Microphone control with visual feedback
- **RTC Audio** - High-quality stereo audio with echo cancellation, noise
  suppression, and auto gain control
- **TypeScript** - Full type safety with Agora SDK and UIKit types
- **React 19 & Next.js 16** - Latest React features and patterns

## Architecture

This sample application uses pnpm workspace packages for the SDK and UI Kit:

**Workspace Dependencies:**

- `@agora/conversational-ai` - Core SDK from
  `../agent-toolkit/conversational-ai-api`
- `@agora/conversational-ai-react` - React hooks from `../agent-toolkit/react`
- `@agora/agent-ui-kit` - UI components from `../agent-ui-kit`

**Key Components:**

1. **ConversationalAIAPI** - Main SDK for managing voice AI connections
2. **RTCHelper** - Handles Agora RTC audio connections
3. **SubRenderController** - Manages real-time transcription rendering
4. **UI Components** - Pre-built components for chat, audio visualization,
   buttons, and agent state

## Prerequisites

- Node.js 18+
- Python backend running on port 8082 (see `../simple-backend/`)

## Configuration

This client runs on port **8083** and connects to the backend on port **8082**.

## Quick Start

**Install dependencies (from repository root):**

```bash
pnpm install
```

**Run development server:**

```bash
pnpm dev
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
   pnpm dev
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
│   ├── utils.ts                 # Utility functions (cn, markdown renderer)
│   └── theme/                   # Theme utilities
├── icons/
│   └── PhoneReceiver.tsx        # Custom icons
├── COMPARISON.md                # Comparison with other implementations
├── package.json                 # Dependencies
└── README.md                    # This file
```

## Key Implementation Details

### MessageEngine Integration

The MessageEngine handles real-time transcription messages from the Agora RTC
stream:

```typescript
import {
  MessageEngine,
  EMessageEngineMode,
  IMessageListItem,
} from "@/lib/message-engine"

const engine = new MessageEngine({
  rtcEngine: client, // Agora RTC client
  renderMode: EMessageEngineMode.AUTO, // AUTO, TEXT, or WORD
  callback: (messages) => {
    // Filter completed messages vs in-progress
    const completedMessages = messages.filter((msg) => msg.status !== 0)
    const inProgress = messages.find((msg) => msg.status === 0)

    setMessageList(completedMessages)
    setCurrentInProgressMessage(inProgress || null)
  },
})
```

**Rendering Modes:**

- `AUTO` - Automatically determines best mode based on message content
- `TEXT` - Processes messages as complete text blocks
- `WORD` - Word-by-word rendering with timing information

### ConvoTextStream Component

Displays transcriptions in a fixed-position chat window (bottom-right):

```typescript
<ConvoTextStream
  messageList={messageList}
  currentInProgressMessage={currentInProgressMessage}
  agentUID="0"
  messageSource="rtc"
/>
```

**Features:**

- Auto-opens on first message
- Auto-scroll with manual override detection
- Supports streaming (in-progress) messages with pulse animation
- Markdown rendering
- Collapsible/expandable with message count indicator
- Avatar display (AI vs User)

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

### Microphone Button

Controls microphone with live waveform visualization:

```typescript
<MicButton
  state={micState}  // "idle" | "listening" | "processing" | "error"
  onClick={toggleMute}
/>
```

**States:**

- `idle` - Not active
- `listening` - Active and listening (shows waveform)
- `processing` - Processing audio
- `error` - Microphone error

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
} = useAgoraVoiceClient()
```

**Responsibilities:**

- Agora client lifecycle management
- MessageEngine initialization and cleanup
- Microphone track creation with AEC/ANS/AGC
- Remote user (agent) audio subscription and playback
- Agent speaking state detection
- Mute/unmute functionality

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
- **UI Components**: Agora AI UIKit (package branch)
- **RTC SDK**: agora-rtc-sdk-ng v4.24+
- **Icons**: lucide-react
- **Animations**: @lottiefiles/dotlottie-react

## Contributing

When adding new features:

1. Use existing agora-ai-uikit components when possible
2. Keep imports using `@/` alias for consistency
3. Update TypeScript types appropriately
4. Test build with `npm run build` before committing
5. Update this README if adding new major features

## License

MIT
