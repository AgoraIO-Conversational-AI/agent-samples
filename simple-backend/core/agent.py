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
            "voice": query_params.get('voice_id', constants["OPENAI_TTS_VOICE"]),
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
                "id": query_params.get('voice_id', constants["CARTESIA_VOICE_ID"])
            }
        }

    elif tts_vendor == "rime":
        tts_config["params"] = {
            "api_key": constants["RIME_API_KEY"],
            "speaker": query_params.get('rime_speaker', constants["RIME_SPEAKER"]),
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


def build_avatar_config(avatar_enabled, avatar_vendor, constants, channel, agent_video_token, query_params=None):
    """
    Builds avatar configuration based on vendor.

    Args:
        avatar_enabled: Whether avatar is enabled
        avatar_vendor: The avatar vendor name
        constants: Dictionary of constants
        channel: The channel name
        agent_video_token: Token for the avatar video stream
        query_params: Optional query parameters for overrides

    Returns:
        Dictionary containing avatar configuration, or None if disabled
    """
    if not avatar_enabled:
        return None

    query_params = query_params or {}

    if avatar_vendor == "heygen":
        return {
            "enable": True,
            "vendor": "heygen",
            "params": {
                "api_key": constants["HEYGEN_API_KEY"],
                "avatar_id": query_params.get('heygen_avatar_id', constants["HEYGEN_AVATAR_ID"]),
                "quality": query_params.get('heygen_quality', constants["HEYGEN_QUALITY"]),
                "agora_appid": constants["APP_ID"],
                "agora_token": agent_video_token,
                "agora_channel": channel,
                "agora_uid": constants["AGENT_VIDEO_UID"],
                "activity_idle_timeout": int(query_params.get('heygen_idle_timeout', constants["HEYGEN_ACTIVITY_IDLE_TIMEOUT"]))
            }
        }
    elif avatar_vendor == "anam":
        # For Anam BETA with no APP_CERTIFICATE, agora_token is the BETA APP_ID
        # If there's a real token (agent_video_token), use that instead
        agora_token_value = agent_video_token if agent_video_token else constants["ANAM_BETA_APP_ID"]

        return {
            "vendor": "anam",
            "enable": True,
            "params": {
                "agora_token": agora_token_value,
                "agora_uid": query_params.get('anam_uid', constants.get("AGENT_VIDEO_UID", "49345")),
                "anam_api_key": query_params.get('anam_api_key', constants.get("ANAM_API_KEY", "")),
                "anam_base_url": query_params.get('anam_base_url', constants.get("ANAM_BASE_URL", "https://api.anam.ai/v1")),
                "anam_avatar_id": query_params.get('anam_avatar_id', constants.get("ANAM_AVATAR_ID", ""))
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

    # Get TTS and ASR vendors
    tts_vendor = query_params.get('tts_vendor', constants["TTS_VENDOR"])
    asr_vendor = query_params.get('asr_vendor', constants["ASR_VENDOR"])

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

    # Get other settings
    max_history = int(query_params.get('max_history', constants["MAX_HISTORY"]))
    idle_timeout = int(query_params.get('idle_timeout', constants["IDLE_TIMEOUT"]))
    vad_silence_duration = int(query_params.get('vad_silence_duration_ms', constants["VAD_SILENCE_DURATION_MS"]))
    enable_aivad = query_params.get('enable_aivad', constants["ENABLE_AIVAD"]).lower() == "true"

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

    # Get avatar settings early to determine remote_rtc_uids and token
    avatar_enabled = query_params.get('avatar_enabled', constants["AVATAR_ENABLED"]).lower() == "true"
    avatar_vendor = query_params.get('avatar_vendor', constants["AVATAR_VENDOR"])

    # Determine token value
    # Anam BETA uses empty string for token (per working curl from Agora developer)
    # Regular mode uses APP_ID (since no certificate)
    is_anam_avatar = avatar_enabled and avatar_vendor == "anam"
    app_id_for_token = "" if is_anam_avatar else constants["APP_ID"]

    # When avatar is enabled, can't use wildcard "*" for remote_rtc_uids
    # Must specify exact user UID
    remote_rtc_uids = [constants["USER_UID"]] if avatar_enabled else ["*"]

    # Build properties
    properties = OrderedDict([
        ("channel", channel),
        ("token", app_id_for_token),  # Empty string for Anam BETA, regular app_id otherwise
        ("agent_rtc_uid", constants["AGENT_UID"]),
        ("agent_rtm_uid", f"{constants['AGENT_UID']}-{channel}"),
        ("remote_rtc_uids", remote_rtc_uids),
        ("advanced_features", {
            "enable_bhvs": True,
            "enable_rtm": True,
            "enable_aivad": enable_aivad,
            "enable_sal": False
        }),
        ("enable_string_uid", False),
        ("idle_timeout", idle_timeout),
        ("llm", llm_config),
        ("vad", {
            "silence_duration_ms": vad_silence_duration
        }),
        ("asr", asr_config),
        ("tts", tts_config),
        ("parameters", {
            "enable_flexible": True,
            "enable_metrics": True,
            "enable_error_message": True,
            "enable_dump": True,
            "dump_params": {
                "enable_downstream_3a": True,
                "enable_upstream_3a": True,
                "enable_tts": True
            },
            "aivad": {
                "max_history": 2,
                "force_threshold": 3000
            },
            "output_audio_codec": "OPUSFB",
            "audio_scenario": "default",
            "transcript": {
                "enable": True,
                "protocol_version": "v2",
                "enable_words": False
            }
        })
    ])

    # Add avatar configuration if enabled
    if avatar_enabled:
        # For Anam BETA, we don't need a real token (it uses app_id instead)
        # So pass agent_video_token even if it's empty string
        avatar_config = build_avatar_config(
            avatar_enabled,
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
    # Check if using Anam BETA avatar
    is_anam_beta = (
        agent_payload.get("properties", {}).get("avatar", {}).get("vendor") == "anam"
    )

    if is_anam_beta:
        # Use BETA endpoint for Anam avatar
        app_id = constants.get("ANAM_BETA_APP_ID")
        beta_endpoint = constants.get("ANAM_BETA_ENDPOINT")
        agent_api_url = f"{beta_endpoint}/{app_id}/join"

        # Use BETA credentials
        beta_creds = constants.get("ANAM_BETA_CREDENTIALS")
        import base64
        auth_header = "Basic " + base64.b64encode(beta_creds.encode()).decode()

        print(f"🎭 Using Anam BETA endpoint: {agent_api_url}")
    else:
        # Use regular endpoint
        agent_api_url = f"{constants['AGENT_API_BASE_URL']}/{constants['APP_ID']}/join"
        auth_header = constants["AGENT_AUTH_HEADER"]

    url_parts = urllib.parse.urlparse(agent_api_url)
    host = url_parts.netloc
    path = url_parts.path

    conn = http.client.HTTPSConnection(host, timeout=30)

    headers = {
        "Content-Type": "application/json",
        "Authorization": auth_header
    }

    payload_json = json.dumps(agent_payload, indent=2)

    print(f"Sending agent to Agora ConvoAI:")
    print(f"URL: {agent_api_url}")
    print(f"🔧 enable_rtm: {agent_payload['properties']['advanced_features']['enable_rtm']}")
    print(f"🔧 enable_bhvs: {agent_payload['properties']['advanced_features']['enable_bhvs']}")

    # Optional curl dump (disabled by default to avoid exposing API keys)
    enable_curl_dump = constants.get("ENABLE_CURL_DUMP", "false").lower() == "true"

    if enable_curl_dump:
        # Print equivalent curl command for debugging
        payload_compact = json.dumps(agent_payload)
        curl_cmd = f"curl -X POST '{agent_api_url}' \\\n  -H 'Authorization: {auth_header}' \\\n  -H 'Content-Type: application/json' \\\n  -d '{payload_compact}'"
        print(f"\n📋 Equivalent curl command:\n{curl_cmd}\n")

        # Write curl command to file with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        curl_file_path = f"/tmp/agora_curl_{timestamp}.sh"

        # Write prettified version to file
        payload_pretty = json.dumps(agent_payload, indent=2)
        curl_file_content = f"""#!/bin/bash
# Agora ConvoAI Request
# Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Channel: {channel}

curl -X POST '{agent_api_url}' \\
  -H 'Authorization: {auth_header}' \\
  -H 'Content-Type: application/json' \\
  -d '{payload_pretty}'
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
    hangup_api_url = f"{constants['AGENT_API_BASE_URL']}/{constants['APP_ID']}/agents/{agent_id}/leave"

    url_parts = urllib.parse.urlparse(hangup_api_url)
    host = url_parts.netloc
    path = url_parts.path

    conn = http.client.HTTPSConnection(host, timeout=30)

    headers = {
        "Content-Type": "application/json",
        "Authorization": constants["AGENT_AUTH_HEADER"]
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
