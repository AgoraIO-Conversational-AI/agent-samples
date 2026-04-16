# Agent Lifecycle

> **When to Read This:** Load this document when modifying agent creation logic, adding vendor support, debugging API errors, or understanding the custom LLM registration flow.

## Overview

The agent lifecycle spans creation, conversation, and teardown. The backend orchestrates agent creation through the Agora ConvoAI API, optionally registers with a custom LLM server, and handles cleanup on disconnect.

## Creation Flow

```
GET /start-agent?channel=X&profile=voice
    │
    ▼
initialize_constants("voice")
    │ load <PROFILE>_* env vars
    ▼
build_token_with_rtm(channel, uid)
    │ v007 token with RTC + RTM services
    ▼
create_agent_payload()
    ├── build_tts_config()      # vendor-specific TTS
    ├── build_asr_config()      # vendor-specific ASR
    ├── build_mllm_config()     # optional multimodal LLM
    ├── build_avatar_config()   # optional avatar vendor
    ├── build_mcp_servers()     # optional MCP tools
    │   Assembles full JSON payload for Agora API
    ▼
send_agent_to_channel(payload)
    │ POST /api/conversational-ai-agent/v2/projects/{APP_ID}/join
    │ Auth: v007 token or Basic auth
    ▼
Return to client: {token, uid, channel, appid, agent_response}
    │
    ▼ (async, non-blocking)
register_agent_with_custom_llm()
    │ POST /register-agent to custom LLM server
    │ Background thread (daemon=True)
    │ Silently fails if custom LLM is down
```

## Payload Structure (Simplified)

```json
{
  "name": "<channel>_agent",
  "properties": {
    "channel": "<channel>",
    "token": "<v007_token>",
    "agent_rtc_uid": "<agent_uid>",
    "remote_rtc_uids": ["<user_uid>"],
    "enable_rtm": true,
    "advanced_features": {
      "enable_aivad": true
    },
    "llm": { ... },
    "tts": { ... },
    "asr": { ... },
    "mllm": { ... },      // optional
    "avatar": { ... },    // optional
    "parameters": {
      "transcript": { "enable": true }
    }
  }
}
```

## Teardown Flow

```
GET /hangup-agent?agent_id=X
    │
    ▼
POST /api/conversational-ai-agent/v2/projects/{APP_ID}/leave
    │ body: {"agent_id": X}
    ▼
Return to client: {agent_response}
    │
    ▼ (async, non-blocking)
unregister_agent_with_custom_llm()
    │ POST /unregister-agent to custom LLM server
```

## Vendor-Specific Config Patterns

### TTS Vendors

| Vendor       | Required Keys                 | Notes                   |
| ------------ | ----------------------------- | ----------------------- |
| `rime`       | `TTS_API_KEY`, `TTS_VOICE_ID` | Default sample rate 24k |
| `elevenlabs` | `TTS_API_KEY`, `TTS_VOICE_ID` | Default sample rate 24k |
| `openai`     | `TTS_API_KEY`, `TTS_VOICE_ID` | —                       |
| `cartesia`   | `TTS_API_KEY`, `TTS_VOICE_ID` | —                       |

### Avatar Vendors

| Vendor   | Required Keys | Notes                             |
| -------- | ------------- | --------------------------------- |
| `heygen` | `AVATAR_ID`   | ID format: `Name_Position_public` |
| `anam`   | `AVATAR_ID`   | —                                 |
| `akool`  | `AVATAR_ID`   | MUST use 16kHz sample rate        |

### MLLM Vendors

| Vendor            | Required Keys                                 | Notes               |
| ----------------- | --------------------------------------------- | ------------------- |
| `vertexai`        | `MLLM_API_KEY`, `MLLM_MODEL`, `MLLM_LOCATION` | Location NOT region |
| `openai_realtime` | `MLLM_API_KEY`, `MLLM_MODEL`                  | Built-in TTS        |

## Pipeline Mode Feature Composition

Pipeline mode (`PIPELINE_ID` set) delegates TTS/ASR/AIVAD to the pipeline. Not all optional features compose with it:

| Feature     | With Pipeline? | Notes                                                                      |
| ----------- | -------------- | -------------------------------------------------------------------------- |
| Custom LLM  | Yes            | `LLM_VENDOR=custom` + `LLM_URL` builds a full `properties.llm` block       |
| MCP Servers | No             | `build_mcp_servers()` only called in non-pipeline `create_agent_payload()` |
| Avatar      | Yes            | Avatar config is connection-level, independent of pipeline                 |
| MLLM        | Yes            | MLLM config applied via pipeline overrides                                 |
| Transcript  | Yes            | `parameters.transcript` is connection-level (NOT in pipeline config)       |

If you set `MCP_SERVERS` with a pipeline profile, the MCP config is silently ignored — no error, no servers attached.

## Common API Errors

| HTTP Code | Cause                           | Fix                                |
| --------- | ------------------------------- | ---------------------------------- |
| 400       | Invalid avatar ID               | Check avatar ID format             |
| 400       | Missing MLLM location           | Set `<P>_MLLM_LOCATION`            |
| 401       | Invalid credentials             | Check APP*CERTIFICATE, CUSTOMER*\* |
| 409       | Agent already exists in channel | Call hangup first                  |

## See Also

- [Back to Architecture](../02_architecture.md)
- [Back to Interfaces](../06_interfaces.md)
