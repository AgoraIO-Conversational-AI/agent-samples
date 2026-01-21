"""
Agent payload building and API communication for Agora ConvoAI
"""

import json
import http.client
import urllib.parse
from collections import OrderedDict


def build_tts_config(tts_vendor, constants, query_params=None):
    """
    Builds TTS configuration based on vendor.

    Args:
        tts_vendor: The TTS vendor name
        constants: Dictionary of constants
        query_params: Optional query parameters for overrides

    Returns:
        Dictionary containing TTS configuration
    """
    query_params = query_params or {}

    tts_config = {
        "vendor": tts_vendor
    }

    if tts_vendor == "elevenlabs":
        voice_id = query_params.get('voice_id', constants["TTS_VOICE_ID"])
        if not voice_id:
            raise ValueError("TTS_VOICE_ID is required for ElevenLabs")

        tts_config["params"] = {
            "key": constants["TTS_KEY"],
            "model_id": query_params.get('tts_model', constants["ELEVENLABS_MODEL"]),
            "voice_id": voice_id,
            "stability": float(query_params.get('voice_stability', constants["ELEVENLABS_STABILITY"])),
            "sample_rate": int(query_params.get('sample_rate', constants["TTS_SAMPLE_RATE"]))
        }

    elif tts_vendor == "openai":
        tts_config["params"] = {
            "api_key": constants["TTS_KEY"],
            "model": query_params.get('tts_model', constants["OPENAI_TTS_MODEL"]),
            "voice": query_params.get('voice_id', constants["TTS_VOICE_ID"]),
            "response_format": "pcm",
            "speed": float(query_params.get('voice_speed', constants["TTS_SPEED"]))
        }

    elif tts_vendor == "cartesia":
        tts_config["params"] = {
            "api_key": constants["TTS_KEY"],
            "model_id": query_params.get('tts_model', constants["CARTESIA_MODEL"]),
            "sample_rate": int(query_params.get('sample_rate', constants["TTS_SAMPLE_RATE"])),
            "voice": {
                "mode": "id",
                "id": query_params.get('voice_id', constants["TTS_VOICE_ID"])
            }
        }

    elif tts_vendor == "rime":
        tts_config["params"] = {
            "api_key": constants["TTS_KEY"],
            "speaker": query_params.get('voice_id', constants["TTS_VOICE_ID"]),
            "modelId": query_params.get('rime_model_id', constants["RIME_MODEL_ID"]),
            "lang": query_params.get('rime_lang', constants["RIME_LANG"]),
            "samplingRate": int(query_params.get('rime_sampling_rate', constants["RIME_SAMPLING_RATE"])),
            "speedAlpha": float(query_params.get('rime_speed_alpha', constants["RIME_SPEED_ALPHA"]))
        }
    else:
        raise ValueError(f"Unsupported TTS vendor: {tts_vendor}")

    return tts_config


def build_asr_config(asr_vendor, constants, query_params=None):
    """
    Builds ASR configuration based on vendor.

    Args:
        asr_vendor: The ASR vendor name
        constants: Dictionary of constants
        query_params: Optional query parameters for overrides

    Returns:
        Dictionary containing ASR configuration
    """
    query_params = query_params or {}

    asr_config = {
        "vendor": asr_vendor
    }

    if asr_vendor == "ares":
        # Ares is built into Agora, just needs language
        asr_config["language"] = query_params.get('asr_language', constants["ASR_LANGUAGE"])

    elif asr_vendor == "deepgram":
        asr_config["params"] = {
            "key": constants["DEEPGRAM_KEY"],
            "model": query_params.get('deepgram_model', constants["DEEPGRAM_MODEL"]),
            "language": query_params.get('deepgram_language', constants["DEEPGRAM_LANGUAGE"])
        }
    else:
        # Default fallback - just set language
        asr_config["language"] = query_params.get('asr_language', constants["ASR_LANGUAGE"])

    return asr_config


def build_mllm_config(constants, query_params=None):
    """
    Builds MLLM (Multimodal LLM) configuration for Gemini Live.

    Args:
        constants: Dictionary of constants
        query_params: Optional query parameters for overrides

    Returns:
        Dictionary containing MLLM configuration
    """
    query_params = query_params or {}
    import base64

    # Get adc_credentials_string - can be stringified JSON or base64
    adc_credentials = query_params.get('adc_credentials_string', constants.get("MLLM_ADC_CREDENTIALS_STRING", ""))

    # If it looks like JSON (starts with {), use it directly; otherwise assume base64
    if adc_credentials and not adc_credentials.strip().startswith("{"):
        try:
            adc_credentials = base64.b64decode(adc_credentials).decode('utf-8')
        except Exception:
            # If base64 decode fails, use as-is
            pass

    mllm_config = {
        "predefined_tools": ["_publish_message"],
        "vendor": query_params.get('mllm_vendor', constants.get("MLLM_VENDOR", "vertexai")),
        "url": query_params.get('mllm_url', constants.get("MLLM_URL", "")),
        "api_key": "",
        "messages": [
            {
                "role": "system",
                "content": query_params.get('prompt', constants.get("DEFAULT_PROMPT", "You are a friendly assistant."))
            }
        ],
        "params": {
            "model": query_params.get('mllm_model', constants.get("MLLM_MODEL", "gemini-live-2.5-flash-preview-native-audio-09-2025")),
            "temperature": 0.9,
            "instructions": query_params.get('prompt', constants.get("DEFAULT_PROMPT", "You are a friendly assistant.")),
            "voice": query_params.get('mllm_voice', constants.get("MLLM_VOICE", "Charon")),
            "max_tokens": 3000,
            "affective_dialog": False,
            "proactive_audio": False,
            "adc_credentials_string": adc_credentials,
            "project_id": query_params.get('mllm_project_id', constants.get("MLLM_PROJECT_ID", "")),
            "location": query_params.get('mllm_location', constants.get("MLLM_LOCATION", "us-central1")),
            "transcribe_agent": query_params.get('mllm_transcribe_agent', constants.get("MLLM_TRANSCRIBE_AGENT", "true")).lower() == "true",
            "transcribe_user": query_params.get('mllm_transcribe_user', constants.get("MLLM_TRANSCRIBE_USER", "true")).lower() == "true"
        },
        "output_modalities": ["audio"],
        "max_history": 20,
        "greeting_message": query_params.get('greeting', constants.get("DEFAULT_GREETING", "Hey There Sir")),
        "failure_message": query_params.get('failure_message', constants.get("DEFAULT_FAILURE_MESSAGE", "Something went wrong"))
    }

    return mllm_config


def build_avatar_config(avatar_vendor, constants, channel, agent_video_token, query_params=None):
    """
    Builds avatar configuration based on vendor.

    Args:
        avatar_vendor: The avatar vendor name (heygen, anam, or None)
        constants: Dictionary of constants
        channel: The channel name
        agent_video_token: Token for the avatar video stream
        query_params: Optional query parameters for overrides

    Returns:
        Dictionary containing avatar configuration, or None if no vendor
    """
    if not avatar_vendor:
        return None

    query_params = query_params or {}

    # Validate generic avatar credentials
    if not constants.get("AVATAR_API_KEY"):
        raise ValueError(
            f"AVATAR_API_KEY is required when AVATAR_VENDOR={avatar_vendor}. "
            f"Set AVATAR_API_KEY in your .env file."
        )
    if not constants.get("AVATAR_ID"):
        raise ValueError(
            f"AVATAR_ID is required when AVATAR_VENDOR={avatar_vendor}. "
            f"Set AVATAR_ID in your .env file."
        )

    if avatar_vendor == "heygen":
        # For HeyGen, agora_token is the APP_ID if no real token
        agora_token_value = agent_video_token if agent_video_token else constants["APP_ID"]

        return {
            "vendor": "heygen",
            "enable": True,
            "params": {
                "api_key": constants["AVATAR_API_KEY"],
                "quality": query_params.get('heygen_quality', constants["HEYGEN_QUALITY"]),
                "agora_uid": constants["AGENT_VIDEO_UID"],
                "agora_token": agora_token_value,
                "avatar_id": constants["AVATAR_ID"],
                "disable_idle_timeout": False,
                "activity_idle_timeout": int(query_params.get('heygen_idle_timeout', constants["HEYGEN_ACTIVITY_IDLE_TIMEOUT"]))
            }
        }
    elif avatar_vendor == "anam":
        # For Anam, agora_token is the APP_ID if no real token
        agora_token_value = agent_video_token if agent_video_token else constants["APP_ID"]

        return {
            "vendor": "anam",
            "enable": True,
            "params": {
                "agora_token": agora_token_value,
                "agora_uid": query_params.get('anam_uid', constants.get("AGENT_VIDEO_UID", "49345")),
                "anam_api_key": constants["AVATAR_API_KEY"],
                "anam_base_url": constants["ANAM_BASE_URL"],
                "anam_avatar_id": constants["AVATAR_ID"]
            }
        }
    else:
        # Placeholder for future avatar vendors
        return None


def create_agent_payload(channel, constants, query_params=None, agent_video_token=None):
    """
    Creates the complete agent payload for Agora ConvoAI.

    Args:
        channel: The channel name
        constants: Dictionary of constants
        query_params: Optional query parameters for overrides
        agent_video_token: Token for avatar video (if avatar enabled)

    Returns:
        OrderedDict containing the complete agent payload
    """
    query_params = query_params or {}

    # Check if MLLM mode is enabled
    enable_mllm = query_params.get('enable_mllm', constants.get("ENABLE_MLLM", "false")).lower() == "true"
    print(f"🔍 DEBUG: enable_mllm={enable_mllm}, ENABLE_MLLM from constants={constants.get('ENABLE_MLLM', 'NOT SET')}")

    # Get other settings
    idle_timeout = int(query_params.get('idle_timeout', constants["IDLE_TIMEOUT"]))
    vad_silence_duration = int(query_params.get('vad_silence_duration_ms', constants["VAD_SILENCE_DURATION_MS"]))
    enable_aivad = query_params.get('enable_aivad', constants["ENABLE_AIVAD"]).lower() == "true"

    # MLLM mode: Build mllm config, skip TTS/LLM
    if enable_mllm:
        mllm_config = build_mllm_config(constants, query_params)

        # Get ASR vendor for MLLM mode (still needed)
        asr_vendor = query_params.get('asr_vendor', constants.get("ASR_VENDOR", "ares"))
        asr_config = build_asr_config(asr_vendor, constants, query_params)

        tts_config = None
        llm_config = None
    else:
        # Standard mode: Build TTS and LLM configs
        tts_vendor = query_params.get('tts_vendor', constants.get("TTS_VENDOR"))
        asr_vendor = query_params.get('asr_vendor', constants.get("ASR_VENDOR"))

        if not tts_vendor:
            raise ValueError("TTS_VENDOR must be set via environment variable or query parameter")

        # Build TTS configuration
        tts_config = build_tts_config(tts_vendor, constants, query_params)

        # Build ASR configuration
        asr_config = build_asr_config(asr_vendor, constants, query_params)

        # Get LLM parameters
        llm_url = query_params.get('llm_url', constants["LLM_URL"])
        llm_api_key = query_params.get('llm_api_key', constants["LLM_API_KEY"])
        llm_model = query_params.get('llm_model', constants["LLM_MODEL"])

        # Get prompt and messages
        prompt = query_params.get('prompt', constants["DEFAULT_PROMPT"])
        greeting = query_params.get('greeting', constants["DEFAULT_GREETING"])
        failure_message = query_params.get('failure_message', constants["DEFAULT_FAILURE_MESSAGE"])
        max_history = int(query_params.get('max_history', constants["MAX_HISTORY"]))

        # Build LLM configuration
        llm_config = {
            "url": llm_url,
            "api_key": llm_api_key,
            "system_messages": [
                {
                    "role": "system",
                    "content": prompt
                }
            ],
            "greeting_message": greeting,
            "failure_message": failure_message,
            "max_history": max_history,
            "params": {
                "model": llm_model
            },
            "style": "openai"
        }

        mllm_config = None

    # Get avatar settings early to determine remote_rtc_uids and token
    avatar_vendor = constants.get("AVATAR_VENDOR")

    # Determine token value
    # Anam uses empty string for token (per working curl from Agora developer)
    # Regular mode uses APP_ID (since no certificate)
    is_anam_avatar = avatar_vendor == "anam"
    app_id_for_token = "" if is_anam_avatar else constants["APP_ID"]

    # When avatar is enabled, can't use wildcard "*" for remote_rtc_uids
    # Must specify exact user UID
    remote_rtc_uids = [constants["USER_UID"]] if avatar_vendor else ["*"]

    # Build advanced_features
    advanced_features = {
        "enable_bhvs": True,
        "enable_rtm": True,
        "enable_aivad": enable_aivad,
        "enable_sal": False
    }
    if enable_mllm:
        advanced_features["enable_mllm"] = True
        advanced_features["enable_tools"] = False

    # Build properties
    properties = OrderedDict([
        ("channel", channel),
        ("token", app_id_for_token),  # Empty string for Anam BETA, regular app_id otherwise
        ("agent_rtc_uid", constants["AGENT_UID"]),
        ("agent_rtm_uid", f"{constants['AGENT_UID']}-{channel}"),
        ("remote_rtc_uids", remote_rtc_uids),
        ("advanced_features", advanced_features),
        ("enable_string_uid", False),
        ("idle_timeout", idle_timeout),
    ])

    # Add mllm or llm configuration
    if enable_mllm:
        properties["mllm"] = mllm_config
    else:
        properties["llm"] = llm_config

    # Add VAD configuration
    properties["vad"] = {
        "silence_duration_ms": vad_silence_duration
    }

    # Add ASR configuration
    properties["asr"] = asr_config

    # Add TTS configuration (only in non-MLLM mode)
    if not enable_mllm:
        properties["tts"] = tts_config

    # Add turn_detection for MLLM mode
    if enable_mllm:
        properties["turn_detection"] = {
            "type": query_params.get('turn_detection_type', constants.get("TURN_DETECTION_TYPE", "server_vad"))
        }

    # Add transcript parameters for TTS+LLM mode
    if not enable_mllm:
        properties["parameters"] = {
            "transcript": {
                "enable": True,
                "protocol_version": "v2",
                "enable_words": False
            }
        }

    # Add avatar configuration if vendor is set
    if avatar_vendor:
        # For Anam, we don't need a real token (it uses app_id instead)
        # So pass agent_video_token even if it's empty string
        avatar_config = build_avatar_config(
            avatar_vendor,
            constants,
            channel,
            agent_video_token if agent_video_token else "",
            query_params
        )
        if avatar_config:
            properties["avatar"] = avatar_config

    # Build the complete payload
    payload = OrderedDict([
        ("name", channel),
        ("properties", properties)
    ])

    return payload


def send_agent_to_channel(channel, agent_payload, constants):
    """
    Sends an agent to the specified Agora RTC channel by calling the REST API.

    Args:
        channel: The channel name
        agent_payload: The complete agent payload to send
        constants: Dictionary of constants

    Returns:
        Dictionary with the status code, response body, and success flag
    """
    # Check if using Anam avatar to determine endpoint
    is_anam_avatar = (
        agent_payload.get("properties", {}).get("avatar", {}).get("vendor") == "anam"
    )

    if is_anam_avatar:
        # Use Anam-specific endpoint
        agent_api_url = f"{constants['ANAM_AGENT_ENDPOINT']}/{constants['APP_ID']}/join"
        auth_header = constants["AGENT_AUTH_HEADER"]
        print(f"🎭 Using Anam endpoint: {agent_api_url}")
    else:
        # Use regular endpoint
        agent_api_url = f"{constants['AGENT_ENDPOINT']}/{constants['APP_ID']}/join"
        auth_header = constants["AGENT_AUTH_HEADER"]

    url_parts = urllib.parse.urlparse(agent_api_url)
    host = url_parts.netloc
    path = url_parts.path

    conn = http.client.HTTPSConnection(host, timeout=30)

    headers = {
        "Content-Type": "application/json",
        "Authorization": auth_header
    }

    # Add X-Request-Id for Anam requests
    if is_anam_avatar:
        import uuid
        headers["X-Request-Id"] = str(uuid.uuid4()).replace('-', '')

    payload_json = json.dumps(agent_payload, indent=2)

    print(f"Sending agent to Agora ConvoAI:")
    print(f"URL: {agent_api_url}")
    print(f"🔧 enable_rtm: {agent_payload['properties']['advanced_features']['enable_rtm']}")
    print(f"🔧 enable_bhvs: {agent_payload['properties']['advanced_features']['enable_bhvs']}")

    # Optional curl dump (disabled by default to avoid exposing API keys)
    enable_curl_dump = constants.get("ENABLE_CURL_DUMP", "false").lower() == "true"

    if enable_curl_dump:
        # Build header arguments for curl from the headers dict
        header_args = ""
        for header_name, header_value in headers.items():
            header_args += f"  -H '{header_name}: {header_value}' \\\n"

        # Print equivalent curl command for debugging
        payload_compact = json.dumps(agent_payload)
        curl_cmd = f"curl -X POST '{agent_api_url}' \\\n{header_args}  -d '{payload_compact}'"
        print(f"\n📋 Equivalent curl command:\n{curl_cmd}\n")

        # Write curl command to file with timestamp and profile name
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = constants.get("PROFILE_NAME", "default")
        curl_file_path = f"/tmp/agora_curl_{profile_name}_{timestamp}.sh"

        # Write prettified version to file
        payload_pretty = json.dumps(agent_payload, indent=2)
        curl_file_content = f"""#!/bin/bash
# Agora ConvoAI Request
# Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Channel: {channel}

curl -X POST '{agent_api_url}' \\
{header_args}  -d '{payload_pretty}'
"""

        with open(curl_file_path, 'w') as f:
            f.write(curl_file_content)

        print(f"📝 Curl command saved to: {curl_file_path}")

    print(f"Payload: {payload_json}")

    conn.request("POST", path, payload_json, headers)

    response = conn.getresponse()
    status_code = response.status
    response_text = response.read().decode('utf-8')

    print(f"Response status: {status_code}")
    print(f"Response body: {response_text}")

    conn.close()

    return {
        "status_code": status_code,
        "response": response_text,
        "success": status_code == 200
    }


def hangup_agent(agent_id, constants):
    """
    Sends a hangup request to disconnect the agent.

    Args:
        agent_id: The unique identifier for the agent to hang up
        constants: Dictionary of constants

    Returns:
        Dictionary with the status code, response body, and success flag
    """
    hangup_api_url = f"{constants['AGENT_ENDPOINT']}/{constants['APP_ID']}/agents/{agent_id}/leave"

    url_parts = urllib.parse.urlparse(hangup_api_url)
    host = url_parts.netloc
    path = url_parts.path

    conn = http.client.HTTPSConnection(host, timeout=30)

    headers = {
        "Content-Type": "application/json",
        "Authorization": constants.get("AGENT_AUTH_HEADER") or ""
    }

    conn.request("POST", path, "", headers)

    response = conn.getresponse()
    status_code = response.status
    response_text = response.read().decode('utf-8')

    conn.close()

    return {
        "status_code": status_code,
        "response": response_text,
        "success": status_code == 200
    }
