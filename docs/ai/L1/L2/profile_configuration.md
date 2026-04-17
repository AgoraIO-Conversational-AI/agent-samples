# Profile Configuration

> **When to Read This:** Load this document when adding new profiles, changing vendor configurations, setting up MLLM (multimodal LLM), or debugging configuration issues.

## Overview

The backend uses a profile-based configuration system that loads environment variables dynamically per request. Profiles allow multiple configurations (voice, video, therapy, etc.) to coexist in a single `.env` file.

## How Profiles Work

```python
# Request: GET /start-agent?profile=voice
initialize_constants("voice")
# Loads: VOICE_TTS_VENDOR, VOICE_ASR_VENDOR, VOICE_APP_ID, etc.
```

1. Profile name normalized to lowercase
2. All env vars matching `<PROFILE>_*` pattern are loaded
3. Variables stored in module-level globals in `core/config.py`
4. No fallback — if `VOICE_APP_ID` is empty, it stays empty (does NOT use `APP_ID`)

## Variable Categories

### Core (Required)

```
<PROFILE>_APP_ID=...
<PROFILE>_APP_CERTIFICATE=...
<PROFILE>_CUSTOMER_ID=...
<PROFILE>_CUSTOMER_SECRET=...
```

### TTS (Text-to-Speech)

| Variable              | Values                                     |
| --------------------- | ------------------------------------------ |
| `<P>_TTS_VENDOR`      | `rime`, `elevenlabs`, `openai`, `cartesia` |
| `<P>_TTS_API_KEY`     | Vendor API key                             |
| `<P>_TTS_VOICE_ID`    | Vendor-specific voice identifier           |
| `<P>_TTS_SAMPLE_RATE` | `16000` or `24000` (Akool requires 16000)  |

### ASR (Speech-to-Text)

| Variable           | Values             |
| ------------------ | ------------------ |
| `<P>_ASR_VENDOR`   | `ares`, `deepgram` |
| `<P>_ASR_LANGUAGE` | Language code      |

### MLLM (Multimodal LLM)

| Variable            | Values                                      |
| ------------------- | ------------------------------------------- |
| `<P>_MLLM_VENDOR`   | `vertexai`, `openai_realtime`               |
| `<P>_MLLM_MODEL`    | Model name                                  |
| `<P>_MLLM_API_KEY`  | Vendor API key                              |
| `<P>_MLLM_LOCATION` | Region (e.g., `us-central1`) — NOT `REGION` |

### Avatar

| Variable            | Values                    |
| ------------------- | ------------------------- |
| `<P>_AVATAR_VENDOR` | `heygen`, `anam`, `akool` |
| `<P>_AVATAR_ID`     | Vendor-specific avatar ID |

### Custom LLM

| Variable          | Values                   |
| ----------------- | ------------------------ |
| `<P>_LLM_URL`     | URL of custom LLM server |
| `<P>_LLM_MODEL`   | Model name               |
| `<P>_LLM_API_KEY` | API key for custom LLM   |

### MCP Servers

```
<PROFILE>_MCP_SERVERS=[{"name":"memory","url":"http://localhost:8090/mcp","transport":"streamable_http"}]
```

## Common Configuration Mistakes

| Mistake                            | Correct Form                       |
| ---------------------------------- | ---------------------------------- |
| `VOICE_MLLM_REGION=us-central1`    | `VOICE_MLLM_LOCATION=us-central1`  |
| `VOICE_MLLM_MLLM_VENDOR=vertexai`  | `VOICE_MLLM_VENDOR=vertexai`       |
| Using `APP_ID` as fallback         | Must set `VOICE_APP_ID` explicitly |
| `TTS_SAMPLE_RATE=24000` with Akool | `TTS_SAMPLE_RATE=16000`            |

## See Also

- [Back to Setup](../01_setup.md)
- [Back to Gotchas](../07_gotchas.md)
