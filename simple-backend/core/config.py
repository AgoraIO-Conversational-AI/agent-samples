"""
Configuration and environment variable management with profile support
"""

import os


def get_env_var(var_name, profile=None, default_value=None):
    """
    Gets an environment variable with profile support.
    If profile is provided, it first checks for PROFILE_VAR_NAME.
    If that doesn't exist, it falls back to VAR_NAME.
    If that doesn't exist, it returns the default_value.

    Args:
        var_name: The environment variable name
        profile: Optional profile prefix (uppercased automatically)
        default_value: Default value if neither variable exists

    Returns:
        The value of the environment variable or default_value
    """
    if profile:
        profiled_var_name = f"{profile.upper()}_{var_name}"
        profiled_value = os.environ.get(profiled_var_name)
        if profiled_value is not None:
            return profiled_value

    value = os.environ.get(var_name)
    if value is not None:
        return value

    return default_value


def initialize_constants(profile=None):
    """
    Initialize all constants with profile support and sensible defaults.

    Args:
        profile: Optional profile suffix for environment variables

    Returns:
        Dictionary of constants
    """
    constants = {
        # Required Agora settings (no defaults)
        "APP_ID": get_env_var('APP_ID', profile),
        "APP_CERTIFICATE": get_env_var('APP_CERTIFICATE', profile, ''),
        "AGENT_AUTH_HEADER": get_env_var('AGENT_AUTH_HEADER', profile),
        "AGENT_API_BASE_URL": "https://api.agora.io/api/conversational-ai-agent/v2/projects",

        # Fixed UIDs
        "AGENT_UID": "100",
        "USER_UID": "101",
        "AGENT_VIDEO_UID": "102",

        # Token expiration (in seconds)
        "TOKEN_EXPIRE": 24 * 3600,  # 24 hours
        "PRIVILEGE_EXPIRE": 24 * 3600,  # 24 hours

        # LLM settings
        "LLM_URL": get_env_var('LLM_URL', profile, "https://api.openai.com/v1/chat/completions"),
        "LLM_API_KEY": get_env_var('LLM_API_KEY', profile),
        "LLM_MODEL": get_env_var('LLM_MODEL', profile, "gpt-4o-mini"),

        # TTS settings (vendor required, no default)
        "TTS_VENDOR": get_env_var('TTS_VENDOR', profile),
        "TTS_KEY": get_env_var('TTS_KEY', profile),
        "TTS_VOICE_ID": get_env_var('TTS_VOICE_ID', profile),
        "TTS_SAMPLE_RATE": get_env_var('TTS_SAMPLE_RATE', profile, "24000"),
        "TTS_SPEED": get_env_var('TTS_SPEED', profile, "1.0"),

        # ElevenLabs specific defaults
        "ELEVENLABS_MODEL": get_env_var('ELEVENLABS_MODEL', profile, "eleven_flash_v2_5"),
        "ELEVENLABS_STABILITY": get_env_var('ELEVENLABS_STABILITY', profile, "0.5"),

        # OpenAI TTS specific defaults
        "OPENAI_TTS_MODEL": get_env_var('OPENAI_TTS_MODEL', profile, "tts-1"),
        "OPENAI_TTS_VOICE": get_env_var('OPENAI_TTS_VOICE', profile, "alloy"),

        # Cartesia specific defaults
        "CARTESIA_MODEL": get_env_var('CARTESIA_MODEL', profile, "sonic-3"),
        "CARTESIA_VOICE_ID": get_env_var('CARTESIA_VOICE_ID', profile, "71a7ad14-091c-4e8e-a314-022ece01c121"),

        # Rime TTS specific settings
        "RIME_API_KEY": get_env_var('RIME_API_KEY', profile),
        "RIME_SPEAKER": get_env_var('RIME_SPEAKER', profile, "astra"),
        "RIME_MODEL_ID": get_env_var('RIME_MODEL_ID', profile, "mistv2"),
        "RIME_LANG": get_env_var('RIME_LANG', profile, "eng"),
        "RIME_SAMPLING_RATE": get_env_var('RIME_SAMPLING_RATE', profile, "16000"),
        "RIME_SPEED_ALPHA": get_env_var('RIME_SPEED_ALPHA', profile, "1.0"),

        # ASR settings (default to ares - no API key needed)
        "ASR_VENDOR": get_env_var('ASR_VENDOR', profile, "ares"),
        "ASR_LANGUAGE": get_env_var('ASR_LANGUAGE', profile, "en-US"),

        # Deepgram specific settings (if using deepgram ASR)
        "DEEPGRAM_KEY": get_env_var('DEEPGRAM_KEY', profile),
        "DEEPGRAM_MODEL": get_env_var('DEEPGRAM_MODEL', profile, "nova-3"),
        "DEEPGRAM_LANGUAGE": get_env_var('DEEPGRAM_LANGUAGE', profile, "en"),

        # VAD settings
        "VAD_SILENCE_DURATION_MS": get_env_var('VAD_SILENCE_DURATION_MS', profile, "300"),
        "ENABLE_AIVAD": get_env_var('ENABLE_AIVAD', profile, "true"),

        # Agent settings
        "IDLE_TIMEOUT": get_env_var('IDLE_TIMEOUT', profile, "120"),
        "MAX_HISTORY": get_env_var('MAX_HISTORY', profile, "32"),

        # Debug settings
        "ENABLE_CURL_DUMP": get_env_var('ENABLE_CURL_DUMP', profile, "false"),

        # Avatar settings (off by default)
        "AVATAR_ENABLED": get_env_var('AVATAR_ENABLED', profile, "false"),
        "AVATAR_VENDOR": get_env_var('AVATAR_VENDOR', profile, "heygen"),

        # HeyGen specific settings
        "HEYGEN_API_KEY": get_env_var('HEYGEN_API_KEY', profile),
        "HEYGEN_AVATAR_ID": get_env_var('HEYGEN_AVATAR_ID', profile, "Wayne_20240711"),
        "HEYGEN_QUALITY": get_env_var('HEYGEN_QUALITY', profile, "high"),
        "HEYGEN_ACTIVITY_IDLE_TIMEOUT": get_env_var('HEYGEN_ACTIVITY_IDLE_TIMEOUT', profile, "120"),

        # Anam Avatar BETA settings
        "ANAM_API_KEY": get_env_var('ANAM_API_KEY', profile),
        "ANAM_AVATAR_ID": get_env_var('ANAM_AVATAR_ID', profile),
        "ANAM_BASE_URL": get_env_var('ANAM_BASE_URL', profile, "https://api.anam.ai/v1"),
        "ANAM_BETA_APP_ID": get_env_var('ANAM_BETA_APP_ID', profile),
        "ANAM_BETA_CREDENTIALS": get_env_var('ANAM_BETA_CREDENTIALS', profile),
        "ANAM_BETA_ENDPOINT": get_env_var('ANAM_BETA_ENDPOINT', profile, "https://api-test.agora.io/api/conversational-ai-agent/v2/projects"),

        # Default prompt and messages
        "DEFAULT_PROMPT": get_env_var('DEFAULT_PROMPT', profile,
            "You are a virtual companion. The user can both talk and type to you and you will be sent text. "
            "Say you can hear them if asked. They can also see you as a digital human. "
            "Keep responses to around 10 to 20 words or shorter. Be upbeat and try and keep conversation "
            "going by learning more about the user."),
        "DEFAULT_GREETING": get_env_var('DEFAULT_GREETING', profile, "hi there"),
        "DEFAULT_FAILURE_MESSAGE": get_env_var('DEFAULT_FAILURE_MESSAGE', profile, "Sorry, something went wrong"),
    }

    return constants
