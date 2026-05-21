import json
import urllib.parse
import urllib.request


DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"


def _post_form(url, data):
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ViralCutter/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload)


def start_device_flow(client_id, scope=""):
    if not client_id:
        raise ValueError("OAuth client_id is required")

    payload = {"client_id": client_id}
    if scope:
        payload["scope"] = scope

    result = _post_form(DEVICE_CODE_URL, payload)
    if "error" in result:
        raise RuntimeError(result.get("error_description") or result["error"])

    required = ["device_code", "user_code", "verification_uri", "expires_in", "interval"]
    missing = [k for k in required if k not in result]
    if missing:
        raise RuntimeError(f"Invalid device flow response. Missing: {', '.join(missing)}")

    return result


def exchange_device_token(client_id, device_code, client_secret=""):
    if not client_id:
        raise ValueError("OAuth client_id is required")
    if not device_code:
        raise ValueError("device_code is required")

    payload = {
        "client_id": client_id,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    if client_secret:
        payload["client_secret"] = client_secret

    result = _post_form(ACCESS_TOKEN_URL, payload)

    if "error" in result:
        return {
            "status": "error",
            "error": result.get("error", "unknown_error"),
            "error_description": result.get("error_description", ""),
        }

    access_token = result.get("access_token", "")
    if not access_token:
        return {
            "status": "error",
            "error": "missing_access_token",
            "error_description": "OAuth response did not include access_token.",
        }

    return {
        "status": "ok",
        "access_token": access_token,
        "token_type": result.get("token_type", ""),
        "scope": result.get("scope", ""),
    }
