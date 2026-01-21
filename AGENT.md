# Agent Video Avatar - Session Notes

## Current Status (2026-01-20)

### ✅ WORKING

- **Remote video (avatar) displays correctly** - HeyGen avatar video now shows
- Audio transcription working
- Voice interaction working

### ❌ BROKEN (Regressions to fix)

1. **Local video not showing on reconnect** - Works on first dial, but disappears after ending call and redialing
   - Error: "The play() request was interrupted by a new load request. https://goo.gl/LdLk22"
   - This was reportedly fixed last week but has regressed

2. **Chat display broken** - Only shows "Agent" label on left side, actual message text not visible
   - Need to debug chat/transcript component rendering

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
- Local video (reconnect): ❌ Broken
- Chat display: ❌ Broken

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

⚠️ **DO NOT commit or push until all issues fixed**

- Local video reconnect broken
- Chat display broken
- Need to verify everything works before committing

📝 **Modified node_modules**

- Changes to RTCHelper are in `node_modules/@agora/conversational-ai`
- This will be lost on `npm install` - need to submit PR to upstream library or use patch-package

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
