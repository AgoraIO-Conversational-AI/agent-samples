# <img src="../assets/agora-logo.svg" alt="Agora" width="24" height="24" style="vertical-align: middle; margin-right: 8px;" /> React Video Avatar AI Client

React/Next.js implementation demonstrating video avatar integration with the
Agora Conversational AI SDK and UI Kit.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Layouts](#layouts)
  - [Desktop Layout](#desktop-layout-768px)
  - [Mobile Layout](#mobile-layout-768px)
- [Project Structure](#project-structure)
- [Key Implementation Details](#key-implementation-details)
  - [Video Components](#video-components)
  - [Responsive Layout Strategy](#responsive-layout-strategy)
  - [Voice Interaction](#voice-interaction)
- [Building for Production](#building-for-production)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Video Avatar Display** - Real-time avatar video streaming
- **Local Camera Preview** - User's camera with mirror effect
- **Responsive Layouts** - Adaptive desktop grid and mobile tab layouts
- **Workspace Architecture** - Uses pnpm workspace packages for SDK and UI Kit
- **Voice Interaction** - Full voice AI conversation with transcription
- **MediaStream Rendering** - Multi-instance video display for responsive
  layouts
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

1. **LocalVideoPreview** - Displays local camera with mirror effect
2. **AvatarVideoDisplay** - Shows remote avatar video stream
3. **VideoGrid** - Desktop 2x2 grid layout (40/60 split)
4. **MobileTabs** - Mobile tab switcher for Video and Chat views
5. **ConversationalAIAPI** - Main SDK for managing voice AI connections
6. **RTCHelper** - Handles Agora RTC audio and video connections

## Prerequisites

- Node.js 18+
- Python backend running on port 8082 (see `../simple-backend/`)

## Configuration

This client runs on port **8084** and connects to the backend on port **8082**.

## Quick Start

**Install dependencies (from repository root):**

```bash
pnpm install
```

**Run development server:**

```bash
pnpm dev:video
```

**Open browser:**

```
http://localhost:8084
```

## Usage

**Backend Configuration:**

The backend must be configured with avatar provider credentials and settings.
See `../simple-backend/README.md` for avatar agent configuration details.

**Start Services:**

1. **Start the Backend** (if not already running):

   ```bash
   cd ../simple-backend
   PORT=8082 python3 local_server.py
   ```

2. **Start the React Video Client**:

   ```bash
   pnpm dev:video
   ```

3. **Connect to Agent**:
   - Backend URL should be `http://localhost:8082` (default)
   - Enable "Enable Local Video" to show your camera
   - Enable "Enable Avatar" to show avatar video
   - Click "Start Conversation"
   - Client automatically calls `/start-agent?profile=avatar` to use
     avatar-specific backend configuration

4. **Interact with Agent**:
   - Speak into your microphone
   - See local video in bottom-left (desktop) or Video tab (mobile)
   - See avatar video in right column (desktop) or Video/Chat tabs (mobile)
   - View transcriptions in Chat section
   - Toggle camera and mute with control buttons
   - End call with "End Call" button

## Layouts

### Desktop Layout (≥768px)

2x2 Grid layout with 40/60 column split:

```
┌─────────────┬─────────────┐
│ Chat        │ Avatar      │
│ (40%)       │ Video       │
│             │ (60%)       │
├─────────────┤             │
│ Local Video │ + Controls  │
│ (40%)       │             │
└─────────────┴─────────────┘
```

### Mobile Layout (<768px)

Tab-based layout with two tabs:

**Video Tab:**

- Avatar video (50%)
- Local video (50%)

**Chat Tab:**

- Avatar video (35%)
- Conversation (65%)

Fixed bottom controls for microphone, camera, and end call.

## Project Structure

```
react-video-client-avatar/
├── app/
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Main page
│   └── globals.css              # Tailwind CSS with workspace scanning
├── components/
│   └── VideoAvatarClient.tsx    # Main video client component
├── hooks/
│   ├── use-audio-devices.ts
│   ├── use-is-mobile.ts
│   └── useAgoraVoiceClient.ts   # Custom hook for Agora integration
├── lib/
│   └── utils.ts                 # Utility functions (cn)
├── next.config.ts               # Transpile workspace packages
├── package.json                 # Dependencies
└── README.md                    # This file
```

## Key Implementation Details

### Video Components

Uses MediaStream mode for responsive layouts:

```typescript
import { LocalVideoPreview, AvatarVideoDisplay } from '@agora/ui-kit'
import { useLocalVideo, useRemoteVideo } from '@agora/conversational-ai-react'

// Local camera
const { videoTrack } = useLocalVideo()
<LocalVideoPreview
  videoTrack={videoTrack}
  useMediaStream={true}  // Enables multi-instance rendering
/>

// Avatar video
const { remoteVideoUsersArray } = useRemoteVideo({ client })
const avatarVideoTrack = remoteVideoUsersArray[0]?.videoTrack
<AvatarVideoDisplay
  videoTrack={avatarVideoTrack}
  state={avatarVideoTrack ? "connected" : "disconnected"}
  useMediaStream={true}  // Enables multi-instance rendering
/>
```

**MediaStream Mode** allows the same video track to be displayed in multiple
locations simultaneously (desktop and mobile layouts).

### Responsive Layout Strategy

Uses CSS-based conditional visibility instead of conditional rendering:

```typescript
{/* Desktop - Hidden on mobile */}
<VideoGrid className="hidden md:grid flex-1" ... />

{/* Mobile - Hidden on desktop */}
<div className="flex md:hidden flex-1 flex-col" ... >
  <MobileTabs ... />
</div>
```

This approach ensures video tracks don't need to be moved in the DOM when
switching viewports.

### Voice Interaction

Full voice AI capabilities using the same `useAgoraVoiceClient` hook:

```typescript
const {
  isConnected,
  isMuted,
  micState,
  messageList,
  currentInProgressMessage,
  isAgentSpeaking,
  localAudioTrack,
  joinChannel,
  leaveChannel,
  toggleMute,
  sendMessage,
  rtcHelperRef,
} = useAgoraVoiceClient()
```

## Building for Production

```bash
pnpm build
cd react-video-client-avatar
npm start
```

The build creates an optimized production bundle with:

- Transpiled workspace packages
- Server-side rendering disabled for browser-only components
- TypeScript type checking
- Optimized static pages

## Tech Stack

- **Framework**: Next.js 16 with App Router and Turbopack
- **Language**: TypeScript 5
- **Runtime**: React 19
- **Styling**: Tailwind CSS v4
- **UI Components**: Agora AI UIKit (workspace package)
- **RTC SDK**: agora-rtc-sdk-ng v4.24+
- **Icons**: lucide-react
- **State Management**: React hooks

## Troubleshooting

**Local video not showing:**

- Check camera permissions in browser
- Ensure "Enable Local Video" is checked before connecting
- Check browser console for Agora SDK errors

**Avatar video not appearing:**

- Verify backend has avatar provider credentials configured (see
  `../simple-backend/README.md`)
- Check "Enable Avatar" is checked before connecting
- Verify backend logs for agent creation success

**Layout issues:**

- Refresh page if switching between desktop/mobile viewports
- Check browser width (768px is the breakpoint)

## Contributing

When adding new features:

1. Use existing UI Kit components when possible
2. Update TypeScript types appropriately
3. Test both desktop and mobile layouts
4. Test build with `pnpm build` before committing
5. Update this README if adding new major features

## License

MIT
