"""
Local Flask server for Agora Conversational AI

This is a thin wrapper that:
1. Loads .env file into environment
2. Extracts parameters from HTTP request
3. Calls core business logic (same as Lambda!)
4. Returns HTTP JSON response
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file before importing core modules

from flask import Flask, request, jsonify
from core.config import initialize_constants
from core.tokens import build_token_with_rtm
from core.agent import create_agent_payload, send_agent_to_channel, hangup_agent
from core.utils import generate_random_channel

app = Flask(__name__)


@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/start-agent', methods=['GET'])
def start_agent():
    """
    Start an agent and return connection details.

    Query Parameters:
        channel: Channel name (auto-generated if not provided)
        profile: Profile name for env var overrides
        connect: "true" (default) to start agent, "false" for token-only
        debug: Include debug info in response

    Examples:
        GET /start-agent?channel=test
        GET /start-agent?channel=test&profile=sales
        GET /start-agent?connect=false
    """
    # Get query parameters from HTTP request
    query_params = request.args.to_dict()

    # Get optional profile parameter
    profile = query_params.get('profile')

    # Initialize constants with profile
    constants = initialize_constants(profile)

    # Get or generate channel
    channel = query_params.get('channel') or generate_random_channel(10)

    # Check if token-only mode
    token_only_mode = query_params.get('connect', 'true').lower() == 'false'

    # Check if avatar mode is enabled (determines which APP_ID to use)
    avatar_enabled = query_params.get('avatar_enabled', constants["AVATAR_ENABLED"]).lower() == "true"
    avatar_vendor = query_params.get('avatar_vendor', constants["AVATAR_VENDOR"])
    is_anam_avatar = avatar_enabled and avatar_vendor == "anam"

    # Use BETA APP_ID for Anam avatar, regular APP_ID otherwise
    app_id_to_use = constants["ANAM_BETA_APP_ID"] if is_anam_avatar else constants["APP_ID"]

    # Check if we have APP_CERTIFICATE for token generation
    has_certificate = bool(constants["APP_CERTIFICATE"] and constants["APP_CERTIFICATE"].strip())

    # Generate tokens
    if has_certificate:
        user_token_data = build_token_with_rtm(channel, constants["USER_UID"], constants)
        agent_video_token_data = build_token_with_rtm(channel, constants["AGENT_VIDEO_UID"], constants)
    else:
        user_token_data = {"token": "", "uid": constants["USER_UID"]}
        agent_video_token_data = {"token": "", "uid": constants["AGENT_VIDEO_UID"]}

    # Token-only mode response
    if token_only_mode:
        return jsonify({
            "audio_scenario": "10",
            "token": user_token_data["token"],
            "uid": user_token_data["uid"],
            "channel": channel,
            "appid": app_id_to_use,
            "user_token": user_token_data,
            "agent_video_token": agent_video_token_data,
            "agent": {
                "uid": constants["AGENT_UID"]
            },
            "agent_rtm_uid": f"{constants['AGENT_UID']}-{channel}",
            "enable_string_uid": False,
            "token_generation_method": "v007 tokens with RTC+RTM services" if has_certificate else "APP_ID only (no APP_CERTIFICATE)",
            "agent_response": {
                "status_code": 200,
                "response": {"message": "Token-only mode: tokens generated successfully", "mode": "token_only", "connect": False},
                "success": True
            }
        })

    # Normal flow: create and send agent
    try:
        agent_payload = create_agent_payload(
            channel=channel,
            constants=constants,
            query_params=query_params,
            agent_video_token=agent_video_token_data["token"]
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Send agent to channel
    agent_response = send_agent_to_channel(channel, agent_payload, constants)

    # Build response
    response_data = {
        "audio_scenario": "10",
        "token": user_token_data["token"],
        "uid": user_token_data["uid"],
        "channel": channel,
        "appid": app_id_to_use,
        "user_token": user_token_data,
        "agent_video_token": agent_video_token_data,
        "agent": {
            "uid": constants["AGENT_UID"]
        },
        "agent_rtm_uid": f"{constants['AGENT_UID']}-{channel}",
        "enable_string_uid": False,
        "agent_response": agent_response
    }

    # Add debug info if requested
    if 'debug' in query_params:
        response_data["debug"] = {
            "agent_payload": agent_payload,
            "channel": channel,
            "api_url": f"{constants['AGENT_API_BASE_URL']}/{constants['APP_ID']}/join",
            "token_generation_method": "v007 tokens with RTC+RTM services" if has_certificate else "APP_ID only (no APP_CERTIFICATE)",
            "has_app_certificate": has_certificate
        }

    return jsonify(response_data)


@app.route('/hangup-agent', methods=['GET'])
def hangup_agent_route():
    """
    Disconnect an agent from the channel.

    Query Parameters:
        agent_id: The agent ID to disconnect (required)
        profile: Profile name for env var overrides

    Example:
        GET /hangup-agent?agent_id=abc123
    """
    # Get query parameters
    query_params = request.args.to_dict()

    # Get optional profile parameter
    profile = query_params.get('profile')

    # Initialize constants
    constants = initialize_constants(profile)

    # Check for required agent_id
    if 'agent_id' not in query_params:
        return jsonify({"error": "Missing agent_id parameter"}), 400

    agent_id = query_params['agent_id']
    hangup_response = hangup_agent(agent_id, constants)

    return jsonify({
        "agent_response": hangup_response
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "agora-convoai-backend"})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8081))
    print("=" * 60)
    print("Agora ConvoAI Local Server")
    print("=" * 60)
    print(f"Starting Flask server on http://0.0.0.0:{port}")
    print("\nEndpoints:")
    print("  GET /start-agent?channel=test")
    print("  GET /hangup-agent?agent_id=xxx")
    print("  GET /health")
    print("\nPress CTRL+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
