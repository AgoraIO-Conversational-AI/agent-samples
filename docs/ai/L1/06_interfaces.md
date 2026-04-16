# 06 Interfaces

> Backend HTTP endpoints, Agora API calls, SDK integration points, and message formats.

## Backend HTTP Endpoints

### GET /start-agent

Creates an Agora Conversational AI agent and returns connection details.

| Parameter     | Type   | Required | Description                     |
| ------------- | ------ | -------- | ------------------------------- |
| `channel`     | string | Yes      | Channel name to join            |
| `profile`     | string | No       | Config profile (default: voice) |
| `prompt`      | string | No       | Override system prompt          |
| `greeting`    | string | No       | Override greeting message       |
| `connect`     | string | No       | Connection mode override        |
| `pipeline_id` | string | No       | Pipeline ID for pipeline mode   |
| `debug`       | string | No       | Include redacted debug payload  |

**Response:**

```json
{
  "token": "<v007_token>",
  "uid": "<rtc_uid>",
  "channel": "<channel_name>",
  "appid": "<app_id>",
  "agent": { "agent_id": "...", "create_ts": ... },
  "agent_response": { ... }
}
```

### GET /hangup-agent

| Parameter  | Type   | Required | Description      |
| ---------- | ------ | -------- | ---------------- |
| `agent_id` | string | Yes      | Agent ID to stop |
| `profile`  | string | No       | Config profile   |

### POST /speak

Push text to agent TTS.

```json
{
  "agent_id": "string",
  "text": "string",
  "profile": "string",
  "priority": "APPEND | INTERRUPT"
}
```

### GET /health

Returns `{ "status": "ok", "service": "agora-convoai-backend" }`.

## Agora ConvoAI API Calls (from Backend)

| Method | Endpoint                                                  | Purpose      |
| ------ | --------------------------------------------------------- | ------------ |
| POST   | `/api/conversational-ai-agent/v2/projects/{APP_ID}/join`  | Create agent |
| POST   | `/api/conversational-ai-agent/v2/projects/{APP_ID}/leave` | Stop agent   |
| POST   | `/api/conversational-ai-agent/v2/projects/{APP_ID}/speak` | Push TTS     |

Authorization: v007 token (preferred) or Basic auth header.

## SDK Integration (React Clients)

```typescript
import AgoraRTC from "agora-rtc-sdk-ng";
import AgoraRTM from "agora-rtm";
import { AgoraVoiceAI } from "agora-agent-client-toolkit";
import { AgentVisualizer, Conversation, ... } from "@agora/agent-ui-kit";
```

### RTC Connection

```typescript
const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp9" });
await client.join(appId, channel, token, uid);
const audioTrack = await AgoraRTC.createMicrophoneAudioTrack({
  AEC: true,
  ANS: true,
  AGC: true,
});
await client.publish(audioTrack);
```

### RTM Connection

```typescript
const rtmClient = new AgoraRTM.RTM(appId, rtmUid, { token });
await rtmClient.login();
await rtmClient.subscribe(channel);
```

## Custom LLM Endpoints (Optional)

| Endpoint            | Method | Purpose                         |
| ------------------- | ------ | ------------------------------- |
| `/chat/completions` | POST   | OpenAI-compatible LLM proxy     |
| `/register-agent`   | POST   | Start audio subscriber + Thymia |
| `/unregister-agent` | POST   | Stop audio subscriber + Thymia  |

## MCP Server Configuration

```json
[
  {
    "name": "memory",
    "url": "http://localhost:8090/mcp",
    "transport": "streamable_http"
  }
]
```

Set as `MCP_SERVERS` env var (JSON array).

## Related Deep Dives

- [Agent Lifecycle](deep_dives/agent_lifecycle.md) — Full payload structure, vendor-specific configs
- [Profile Configuration](deep_dives/profile_configuration.md) — Environment variable patterns
