# Cross-Repository Development Guide

**Location**: `agent-samples/assets/AI_SAMPLES_UIKIT_TOOLKIT_DEV.md`

This guide explains how to develop across the three Agora Conversational AI repositories. Read this file at the start of development sessions for context on the workflow, git hooks, and package management.

## Repository Overview

**Repositories**:

- `agent-samples/` - Sample applications (GitHub: AgoraIO-Conversational-AI/agent-samples)
- `agent-toolkit/` - Core SDK (GitHub: AgoraIO-Conversational-AI/agent-toolkit)
- `agent-ui-kit/` - UI components (GitHub: AgoraIO-Conversational-AI/agent-ui-kit)

**Package Installation**: Samples install toolkit and ui-kit from GitHub:

```json
"@agora/conversational-ai": "github:AgoraIO-Conversational-AI/agent-toolkit#main",
"@agora/agent-ui-kit": "github:AgoraIO-Conversational-AI/agent-ui-kit#main"
```

---

## Development Workflow

### When to Edit Each Repository

**agent-toolkit** - Edit when:

- Fixing bugs in RTCHelper, ConversationalAIAPI, or core SDK logic
- Adding new features to the SDK
- Changing SDK interfaces or behavior

**agent-ui-kit** - Edit when:

- Fixing bugs in UI components (MicButton, Message, Response, etc.)
- Adding new UI components
- Changing component props or styling

**agent-samples** - Edit when:

- Fixing bugs in sample apps (VoiceClient, VideoAvatarClient)
- Adding new sample applications
- Updating documentation or configuration

---

## Making Changes to Toolkit or UI-Kit

When fixing issues that require changes to `agent-toolkit` or `agent-ui-kit`:

### 1. Test Changes Locally First

Edit files in `node_modules` for quick testing:

```bash
# Example: Fix bug in RTCHelper
cd agent-samples/react-voice-client
# Edit node_modules/@agora/conversational-ai/helper/rtc.ts
npm run dev  # Test the fix works
```

### 2. Copy Changes to Source Repository

Once the fix works, copy it to the source repo:

```bash
# For toolkit:
cp node_modules/@agora/conversational-ai/helper/rtc.ts \
   ../../../agent-toolkit/packages/conversational-ai/helper/rtc.ts

# For ui-kit:
cp node_modules/@agora/agent-ui-kit/components/MicButton.tsx \
   ../../../agent-ui-kit/packages/agent-ui-kit/components/MicButton.tsx
```

### 3. Update Documentation

Update the README in the repo you modified:

- `agent-toolkit/README.md` - Document new SDK features/APIs
- `agent-ui-kit/README.md` - Document new component props/usage
- `agent-samples/AGENT.md` - Note breaking changes if any

### 4. Commit and Push

```bash
cd agent-toolkit  # or agent-ui-kit
git add .
git commit -m "feat: description"  # or "fix:", "docs:", etc.
git push origin main
```

**⚠️ IMPORTANT - Never Use --no-verify**:

- Never use `git commit --no-verify` or `git commit -n`
- Pre-commit hooks check ESLint, Prettier, secrets, commit message format
- If hooks fail, fix the errors instead of bypassing them
- ESLint errors: `cd <project-dir> && npx eslint <file>`
- Prettier errors: `npx prettier --write <file>`
- Commit-msg hook blocks "claude" references (case-insensitive)

### 5. Update Samples to Use Latest Changes

After pushing to toolkit/ui-kit, samples will automatically get the latest version on next `npm install`:

```bash
cd agent-samples/react-voice-client
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run dev  # Test with latest toolkit/ui-kit from GitHub
```

**Why this works**: The `package.json` references use `github:org/repo#main`, so `npm install` always pulls the latest commit from the `main` branch.

---

## Making Changes to Samples Only

For changes that only affect sample apps (not toolkit/ui-kit):

### 1. Edit and Test

```bash
cd agent-samples/react-voice-client
# Edit files
npm run dev  # Test changes
```

### 2. Fix Linting Before Committing

```bash
# TypeScript/JavaScript:
cd react-voice-client  # or react-video-client-avatar
npx eslint <file>
npx prettier --write <file>

# Markdown:
npx prettier --write AGENT.md simple-backend/README.md
```

### 3. Commit and Push

```bash
cd agent-samples
git add .
git commit -m "feat: description"  # NEVER use --no-verify!
git push origin main
```

---

## Package Version Management

### Current Strategy: Git-Based Installation

Samples install toolkit and ui-kit directly from GitHub main branch:

```json
"@agora/conversational-ai": "github:AgoraIO-Conversational-AI/agent-toolkit#main",
"@agora/agent-ui-kit": "github:AgoraIO-Conversational-AI/agent-ui-kit#main"
```

**Advantages**:

- No need to publish to npm registry
- No version number management
- Samples always get latest fixes on fresh install

**Fresh install process**:

```bash
cd agent-samples/react-voice-client
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Future: NPM Registry Publishing (Not Currently Used)

If switching to versioned npm packages in the future:

**Publishing to npm** (toolkit or ui-kit):

```bash
cd agent-toolkit  # or agent-ui-kit
npm version patch  # or minor/major
npm run build
npm publish
git push origin main --follow-tags
```

**Updating samples**:

```json
"@agora/conversational-ai": "^1.2.3",
"@agora/agent-ui-kit": "^0.5.0"
```

```bash
cd agent-samples/react-voice-client
npm install @agora/conversational-ai@latest
npm install @agora/agent-ui-kit@latest
```

---

## Repository Structure

```
agent-samples/           # Sample applications
├── react-voice-client/
├── react-video-client-avatar/
├── simple-voice-client/
├── complete-voice-client/
└── simple-backend/

agent-toolkit/           # Core SDK (@agora/conversational-ai)
└── packages/
    ├── conversational-ai/  # Main package
    └── react/              # React hooks

agent-ui-kit/            # UI components (@agora/agent-ui-kit)
└── packages/
    └── agent-ui-kit/
```

---

## Architecture Notes

### RTCHelper (Singleton Pattern)

**Audio Methods**:

- `createAudioTrack()` - Create microphone track
- `setMuted(boolean)` - Mute/unmute audio
- `getMuted()` - Get mute state

**Video Methods**:

- `createVideoTrack()` - Create camera track
- `setVideoEnabled(boolean)` - Enable/disable camera
- `getVideoEnabled()` - Get camera state

**Lifecycle**:

- `init(config)` - Initialize with app ID, channel, token, UID
- `join()` - Join RTC channel
- `leave()` - Leave channel and cleanup all tracks
- `destroy()` - Destroy instance

**Subscription Filters** (optional):

```typescript
await rtcHelper.init({
  appId: "...",
  channel: "...",
  token: "...",
  uid: 12345,
  shouldSubscribeAudio: (uid) => uid !== 999, // Skip audio from uid 999
  shouldSubscribeVideo: (uid) => uid === 100, // Only video from uid 100
});
```

### Video Track Lifecycle Best Practices

```typescript
// Create once
await rtcHelper.createVideoTrack({ encoderConfig: "720p_2" });
await rtcHelper.client.publish(rtcHelper.localVideoTrack);

// Toggle (reuse same track)
await rtcHelper.setVideoEnabled(false); // Camera off
await rtcHelper.setVideoEnabled(true); // Camera on

// Cleanup (automatic)
await rtcHelper.leave(); // Stops and closes all tracks
```

**Common Pitfalls**:

- ❌ Don't recreate track on toggle - use `setVideoEnabled()`
- ❌ Don't use `key` prop on video components - causes remounting
- ❌ Don't manually cleanup tracks - RTCHelper handles it
- ✅ Pass `null` to video component when disabled
- ✅ Check `track._isClosed` before using track references

---

## Git Hooks

All three repositories use git hooks to enforce code quality:

### Pre-commit Hook

**Location**: `.git/hooks/pre-commit`

**What it checks**:

- ESLint for TypeScript/JavaScript files
- Prettier formatting for all files
- Secret detection (API keys, tokens, credentials)

**How it works**:

```bash
# For React projects (react-voice-client, react-video-client-avatar):
# Hook cd's into project directory before running ESLint
# This ensures project-specific .eslintrc.js is used

# Example from agent-samples pre-commit:
for file in $TS_FILES; do
  project_dir=$(echo "$file" | cut -d'/' -f1)
  if [[ "$project_dir" == react-* ]]; then
    (cd "$project_dir" && npx eslint "$(basename $(dirname $file))/$(basename $file)")
  fi
done
```

**If pre-commit fails**:

```bash
# Fix ESLint errors:
cd react-voice-client  # or react-video-client-avatar
npx eslint <file>
# Fix errors manually, then re-run to verify

# Fix Prettier errors:
npx prettier --write <file>
```

### Commit-msg Hook

**Location**: `.git/hooks/commit-msg`

**What it checks**:

- Blocks commits with "claude" in the message (case-insensitive)
- Enforces lowercase first character in commit message

**Example failures**:

```bash
git commit -m "Claude helped fix this"
# ❌ Error: commit message must not mention Claude

git commit -m "Fix bug"
# ❌ Error: commit message should start with lowercase
```

**Correct format**:

```bash
git commit -m "fix: video track not re-enabling"
git commit -m "feat: add shouldSubscribe filters to RTCHelper"
git commit -m "docs: update README with video API"
```

### Never Use --no-verify

**⚠️ CRITICAL**: Never use `git commit --no-verify` or `-n` flag

**Why**:

- Bypasses ESLint → introduces linting errors
- Bypasses Prettier → introduces formatting inconsistencies
- Bypasses secrets detection → risk of committing credentials
- Bypasses commit-msg validation → allows blocked words

**If hooks fail**:

- Fix the errors instead of bypassing
- Hooks protect code quality and security
- Hooks ensure consistent style across the team

---

## Quick Reference

### Check Installed Package Versions

```bash
cd agent-samples/react-voice-client
npm list @agora/conversational-ai
npm list @agora/agent-ui-kit
```

### Force Fresh Install

```bash
cd agent-samples/react-voice-client
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Run Backend Tests

```bash
cd agent-samples/simple-backend
pytest                       # All tests
pytest tests/test_agent.py   # Specific file
```

### Dev Servers

```bash
# Backend (port 8082)
cd agent-samples/simple-backend
PORT=8082 python3 local_server.py

# Voice Client (port 8083)
cd agent-samples/react-voice-client
npm run dev

# Video Client (port 8084)
cd agent-samples/react-video-client-avatar
npm run dev
```

---

**Last Updated**: 2026-01-28
