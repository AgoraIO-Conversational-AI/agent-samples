import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

import jwt

from local_server import app


class PasswordLoginAuthTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.client = app.test_client()
        self.constants = {
            "AUTH_JWT_SECRET": "test-jwt-secret",
            "ENCRYPTION_KEY": "a" * 64,
            "AUTH_DATA_DIR": self.tmpdir,
            "ALLOWED_RETURN_ORIGINS": "http://localhost:8084",
            "CONSULTANT_DASHBOARD_URL": "http://127.0.0.1:8090",
            "CONSULTANT_DASHBOARD_INTERNAL_SHARED_SECRET": "secret",
            "CONSULTANT_DASHBOARD_TIMEOUT_SECONDS": "5",
            "AUTH_BRAND_NAME": "MindFix",
            "TWILIO_ACCOUNT_SID": "",
            "TWILIO_AUTH_TOKEN": "",
            "TWILIO_VERIFY_SERVICE_SID": "",
        }

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_password_login_flow_mints_jwt(self):
        with patch("core.auth._get_profile_constants", return_value=self.constants), \
             patch("core.auth.AUTH_DEV_MODE", True), \
             patch(
                 "core.consultant_dashboard.verify_dashboard_client_password",
                 return_value={
                     "status": "verified",
                     "client_id": "client-123",
                     "consultant_id": "consultant-456",
                     "display_name": "Alex Demo",
                     "email": "alex@example.com",
                     "phone_number": "+447700900111",
                 },
             ):
            login_page = self.client.get(
                "/auth/login?profile=therapy&return=http://localhost:8084/?profile=therapy&autoconnect=true"
            )
            self.assertEqual(login_page.status_code, 200)

            send_code = self.client.post(
                "/auth/password-login",
                data={"email": "alex@example.com", "password": "clientpass123"},
            )
            self.assertEqual(send_code.status_code, 200)
            self.assertTrue(send_code.json["success"])
            self.assertEqual(send_code.json["redirect"], "/auth/verify")

            verify = self.client.post("/auth/verify-pin", data={"pin": "000000"})
            self.assertEqual(verify.status_code, 200)
            self.assertTrue(verify.json["success"])

            redirect_url = verify.json["redirect"]
            parsed = urlparse(redirect_url)
            token = parse_qs(parsed.query)["auth_token"][0]
            claims = jwt.decode(token, self.constants["AUTH_JWT_SECRET"], algorithms=["HS256"])
            self.assertEqual(claims["client_id"], "client-123")
            self.assertEqual(claims["email"], "alex@example.com")
            self.assertEqual(claims["name"], "Alex Demo")


if __name__ == "__main__":
    unittest.main()
