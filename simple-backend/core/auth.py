"""
Optional authentication blueprint for Agora ConvoAI.

When AUTH_JWT_SECRET is set for a profile, this blueprint provides:
- Google OAuth login
- Twilio SMS 2FA
- JWT token minting
- User profile storage (encrypted on disk)

When AUTH_JWT_SECRET is not set, all auth is skipped — get_authenticated_user_id()
returns "anonymous" and the system works exactly as before.
"""

import os
import json
import hashlib
import time
import urllib.parse
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, redirect, session, render_template

auth_bp = Blueprint('auth', __name__)

# Dev mode: skip Google OAuth and Twilio SMS for local testing.
# Set AUTH_DEV_MODE=true in .env. PIN is always 000000.
AUTH_DEV_MODE = os.environ.get('AUTH_DEV_MODE', '').lower() == 'true'


# ─── Helpers ───

def _get_profile_constants():
    """Load constants for the profile stored in Flask session."""
    from core.config import initialize_constants
    profile = session.get('auth_profile')
    if profile:
        profile = profile.lower()
    return initialize_constants(profile)


def _hash(value):
    """SHA-256 hash a string."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _normalize_name(name):
    """Normalize a name for hashing: lowercase, strip, collapse whitespace."""
    import re
    return re.sub(r'\s+', ' ', name.strip().lower())


def _normalize_phone(phone):
    """Normalize phone to digits + optional leading +."""
    import re
    digits = re.sub(r'[^\d+]', '', phone.strip())
    # Ensure leading +
    if not digits.startswith('+'):
        # Assume US if 10 digits
        if len(digits) == 10:
            digits = '+1' + digits
        elif len(digits) == 11 and digits.startswith('1'):
            digits = '+' + digits
    return digits


def _get_data_dir(constants):
    """Get the data directory for user profiles."""
    return constants.get('AUTH_DATA_DIR') or './data'


def _get_user_dir(constants, user_id_hash):
    """Get the directory for a specific user."""
    return os.path.join(_get_data_dir(constants), 'users', user_id_hash)


def _encrypt_json(data, encryption_key, user_id_hash):
    """Encrypt a dict as JSON using AES-256-GCM with HKDF-derived key."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes

    master_key = bytes.fromhex(encryption_key)
    salt = os.urandom(16)

    # Derive per-user key via HKDF
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=user_id_hash.encode('utf-8'),
    )
    derived_key = hkdf.derive(master_key)

    nonce = os.urandom(12)
    aesgcm = AESGCM(derived_key)
    plaintext = json.dumps(data).encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # Format: salt(16) + nonce(12) + ciphertext
    return salt + nonce + ciphertext


def _decrypt_json(encrypted_bytes, encryption_key, user_id_hash):
    """Decrypt AES-256-GCM encrypted JSON."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes

    master_key = bytes.fromhex(encryption_key)
    salt = encrypted_bytes[:16]
    nonce = encrypted_bytes[16:28]
    ciphertext = encrypted_bytes[28:]

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=user_id_hash.encode('utf-8'),
    )
    derived_key = hkdf.derive(master_key)

    aesgcm = AESGCM(derived_key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode('utf-8'))


def _load_user_profile(constants, user_id_hash):
    """Load an encrypted user profile from disk. Returns dict or None."""
    encryption_key = constants.get('ENCRYPTION_KEY')
    if not encryption_key:
        return None
    profile_path = os.path.join(_get_user_dir(constants, user_id_hash), 'profile.enc')
    if not os.path.exists(profile_path):
        return None
    try:
        with open(profile_path, 'rb') as f:
            encrypted = f.read()
        return _decrypt_json(encrypted, encryption_key, user_id_hash)
    except Exception as e:
        print(f"[Auth] Failed to load user profile: {e}")
        return None


def _save_user_profile(constants, user_id_hash, profile_data):
    """Save an encrypted user profile to disk."""
    encryption_key = constants.get('ENCRYPTION_KEY')
    if not encryption_key:
        return
    user_dir = _get_user_dir(constants, user_id_hash)
    os.makedirs(user_dir, exist_ok=True)
    sessions_dir = os.path.join(user_dir, 'sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    profile_path = os.path.join(user_dir, 'profile.enc')
    encrypted = _encrypt_json(profile_data, encryption_key, user_id_hash)
    with open(profile_path, 'wb') as f:
        f.write(encrypted)


def _validate_return_url(return_url, constants):
    """Validate return URL against allowed origins to prevent open redirect."""
    if not return_url:
        return False
    allowed = constants.get('ALLOWED_RETURN_ORIGINS', '')
    if not allowed:
        return True  # No restriction configured
    allowed_origins = [o.strip() for o in allowed.split(',') if o.strip()]
    parsed = urllib.parse.urlparse(return_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin in allowed_origins


# ─── Public helper (imported by local_server.py) ───

def get_authenticated_user_id(req, constants):
    """
    Returns (user_id, user_name, error_string).
    user_id is 'anonymous' when auth is not configured for this profile.
    """
    jwt_secret = constants.get('AUTH_JWT_SECRET')
    if not jwt_secret:
        return 'anonymous', '', None

    auth_header = req.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, '', 'Authentication required'

    try:
        import jwt
        claims = jwt.decode(auth_header[7:], jwt_secret, algorithms=['HS256'])
        return claims['user_id'], claims.get('name', ''), None
    except Exception:
        return None, '', 'Invalid or expired session'


# ─── Routes ───

@auth_bp.route('/auth-check', methods=['GET'])
def auth_check():
    """Check if auth is required for this profile and if the current token is valid."""
    from core.config import initialize_constants

    profile = request.args.get('profile', '')
    if profile:
        profile = profile.lower()
    constants = initialize_constants(profile)

    jwt_secret = constants.get('AUTH_JWT_SECRET')
    if not jwt_secret:
        return jsonify({'auth_required': False, 'authenticated': False})

    # Auth is required — check for valid Bearer token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        try:
            import jwt
            claims = jwt.decode(auth_header[7:], jwt_secret, algorithms=['HS256'])
            return jsonify({
                'auth_required': True,
                'authenticated': True,
                'user_name': claims.get('name', ''),
            })
        except Exception:
            pass  # Fall through to unauthenticated

    # Not authenticated — provide auth URL
    return_url = request.args.get('return_url', '')
    auth_url = (
        f"/auth/login?profile={urllib.parse.quote(profile)}"
        f"&return={urllib.parse.quote(return_url)}"
    )
    return jsonify({
        'auth_required': True,
        'authenticated': False,
        'auth_url': auth_url,
    })


@auth_bp.route('/auth/login', methods=['GET'])
def auth_login():
    """Store profile and return URL in session, serve Google sign-in page."""
    profile = request.args.get('profile', '')
    return_url = request.args.get('return', '')

    session['auth_profile'] = profile
    session['auth_return_url'] = return_url

    return render_template('auth/login.html')


@auth_bp.route('/auth/google', methods=['GET'])
def auth_google():
    """Redirect to Google OAuth consent screen."""
    if AUTH_DEV_MODE:
        # Dev mode: skip Google OAuth, use fake identity
        session['google_sub'] = 'dev-user-12345'
        session['google_email'] = 'dev@localhost'
        session['google_name'] = ''
        print('[Auth] DEV MODE: skipping Google OAuth, using fake identity')
        return redirect('/auth/identity')

    constants = _get_profile_constants()
    client_id = constants.get('GOOGLE_CLIENT_ID')
    if not client_id:
        return 'Google OAuth not configured for this profile', 500

    # Build Google OAuth URL
    callback_url = request.url_root.rstrip('/') + '/auth/google/callback'
    params = urllib.parse.urlencode({
        'client_id': client_id,
        'redirect_uri': callback_url,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
    })
    return redirect(f'https://accounts.google.com/o/oauth2/v2/auth?{params}')


@auth_bp.route('/auth/google/callback', methods=['GET'])
def auth_google_callback():
    """Handle Google OAuth callback — exchange code for user info."""
    code = request.args.get('code')
    if not code:
        return 'Missing authorization code', 400

    constants = _get_profile_constants()
    client_id = constants.get('GOOGLE_CLIENT_ID')
    client_secret = constants.get('GOOGLE_CLIENT_SECRET')
    callback_url = request.url_root.rstrip('/') + '/auth/google/callback'

    # Exchange code for tokens
    import urllib.request
    token_data = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': callback_url,
        'grant_type': 'authorization_code',
    }).encode('utf-8')

    try:
        token_req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_resp = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[Auth] Google token exchange failed: {e}")
        return 'Authentication failed', 500

    # Get user info from ID token
    id_token = token_resp.get('id_token')
    if not id_token:
        return 'No ID token received', 500

    # Decode ID token (we trust Google's response since we just exchanged the code)
    import base64
    payload_b64 = id_token.split('.')[1]
    # Add padding
    payload_b64 += '=' * (4 - len(payload_b64) % 4)
    id_claims = json.loads(base64.urlsafe_b64decode(payload_b64))

    session['google_sub'] = id_claims.get('sub')
    session['google_email'] = id_claims.get('email', '')
    session['google_name'] = id_claims.get('name', '')

    return redirect('/auth/identity')


@auth_bp.route('/auth/identity', methods=['GET'])
def auth_identity():
    """Serve name and phone form."""
    if not session.get('google_sub'):
        return redirect('/auth/login?profile=' + urllib.parse.quote(session.get('auth_profile', '')))

    google_name = session.get('google_name', '')
    return render_template('auth/identity.html', google_name=google_name)


@auth_bp.route('/auth/send-code', methods=['POST'])
def auth_send_code():
    """Validate identity and send Twilio verification SMS."""
    google_sub = session.get('google_sub')
    if not google_sub:
        return jsonify({'error': 'Session expired. Please start over.'}), 401

    constants = _get_profile_constants()
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name or not phone:
        return jsonify({'error': 'Name and phone are required.'}), 400

    normalized_name = _normalize_name(name)
    normalized_phone = _normalize_phone(phone)
    name_hash = _hash(normalized_name)
    phone_hash = _hash(normalized_phone)
    user_id_hash = _hash(google_sub + '|' + normalized_name + '|' + normalized_phone)

    # Check if user exists
    existing = _load_user_profile(constants, user_id_hash)
    if existing:
        # Verify all three factors match
        if existing.get('name_hash') != name_hash or existing.get('phone_hash') != phone_hash:
            # Generic error — don't reveal which factor failed
            return jsonify({'error': 'Unable to verify your identity.'}), 403
    else:
        # New user — create profile
        profile_data = {
            'google_sub': google_sub,
            'email': session.get('google_email', ''),
            'name_hash': name_hash,
            'phone_hash': phone_hash,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_login': datetime.now(timezone.utc).isoformat(),
        }
        _save_user_profile(constants, user_id_hash, profile_data)

    # Store for later verification
    session['auth_name'] = name
    session['auth_phone'] = normalized_phone
    session['auth_user_id_hash'] = user_id_hash

    # Send Twilio verification (skipped in dev mode)
    if AUTH_DEV_MODE:
        print(f'[Auth] DEV MODE: skipping Twilio SMS to {normalized_phone}, use PIN 000000')
    else:
        twilio_sid = constants.get('TWILIO_ACCOUNT_SID')
        twilio_token = constants.get('TWILIO_AUTH_TOKEN')
        verify_sid = constants.get('TWILIO_VERIFY_SERVICE_SID')

        if not all([twilio_sid, twilio_token, verify_sid]):
            return jsonify({'error': 'SMS verification not configured.'}), 500

        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            client.verify.v2.services(verify_sid).verifications.create(
                to=normalized_phone,
                channel='sms'
            )
        except Exception as e:
            print(f"[Auth] Twilio send failed: {e}")
            return jsonify({'error': 'Failed to send verification code.'}), 500

    return jsonify({'success': True, 'redirect': '/auth/verify'})


@auth_bp.route('/auth/verify', methods=['GET'])
def auth_verify():
    """Serve PIN entry form."""
    if not session.get('auth_user_id_hash'):
        return redirect('/auth/login?profile=' + urllib.parse.quote(session.get('auth_profile', '')))

    return render_template('auth/verify.html')


@auth_bp.route('/auth/verify-pin', methods=['POST'])
def auth_verify_pin():
    """Validate PIN via Twilio, mint JWT, redirect back to client."""
    user_id_hash = session.get('auth_user_id_hash')
    phone = session.get('auth_phone')
    if not user_id_hash or not phone:
        return jsonify({'error': 'Session expired. Please start over.'}), 401

    pin = request.form.get('pin', '').strip()
    if not pin or len(pin) != 6:
        return jsonify({'error': 'Please enter the 6-digit code.'}), 400

    constants = _get_profile_constants()

    # Verify PIN
    if AUTH_DEV_MODE:
        # Dev mode: accept 000000
        if pin != '000000':
            return jsonify({'error': 'Invalid code. In dev mode, use 000000.'}), 403
        print('[Auth] DEV MODE: PIN 000000 accepted')
    else:
        twilio_sid = constants.get('TWILIO_ACCOUNT_SID')
        twilio_token = constants.get('TWILIO_AUTH_TOKEN')
        verify_sid = constants.get('TWILIO_VERIFY_SERVICE_SID')

        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            check = client.verify.v2.services(verify_sid).verification_checks.create(
                to=phone,
                code=pin
            )
            if check.status != 'approved':
                return jsonify({'error': 'Invalid code. Please try again.'}), 403
        except Exception as e:
            print(f"[Auth] Twilio verify failed: {e}")
            return jsonify({'error': 'Verification failed. Please try again.'}), 500

    # Update last_login
    existing = _load_user_profile(constants, user_id_hash)
    if existing:
        existing['last_login'] = datetime.now(timezone.utc).isoformat()
        _save_user_profile(constants, user_id_hash, existing)

    # Mint JWT
    import jwt as pyjwt
    jwt_secret = constants.get('AUTH_JWT_SECRET')
    now = int(time.time())
    token = pyjwt.encode({
        'user_id': user_id_hash,
        'email': session.get('google_email', ''),
        'name': session.get('auth_name', ''),
        'iat': now,
        'exp': now + 4 * 3600,  # 4 hours
    }, jwt_secret, algorithm='HS256')

    # Redirect back to client
    return_url = session.get('auth_return_url', '')
    if not _validate_return_url(return_url, constants):
        return jsonify({'error': 'Invalid return URL.'}), 400

    # Append auth_token to return URL
    separator = '&' if '?' in return_url else '?'
    redirect_url = f"{return_url}{separator}auth_token={urllib.parse.quote(token)}"

    # Clear auth session data
    for key in ['google_sub', 'google_email', 'google_name', 'auth_name',
                'auth_phone', 'auth_user_id_hash', 'auth_profile', 'auth_return_url']:
        session.pop(key, None)

    return jsonify({'success': True, 'redirect': redirect_url})
