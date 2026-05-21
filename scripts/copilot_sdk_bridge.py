import asyncio
import json
import sys


def _json_out(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


async def _run_with_sdk(input_payload):
    from copilot import CopilotClient
    from copilot.session import PermissionHandler

    prompt = str(input_payload.get("prompt", "")).strip()
    if not prompt:
        return {"ok": False, "error": "empty_prompt"}

    model = str(input_payload.get("model", "gpt-4.1")).strip() or "gpt-4.1"
    github_token = str(input_payload.get("github_token", "")).strip()

    options = {}
    if github_token:
        options["github_token"] = github_token
        options["use_logged_in_user"] = False

    client = CopilotClient(options or None)

    try:
        await client.start()
        session = await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model=model,
        )
        response = await session.send_and_wait(prompt)

        content = ""
        if response is not None and getattr(response, "data", None) is not None:
            content = getattr(response.data, "content", "") or ""

        return {"ok": True, "content": content}
    finally:
        try:
            await client.stop()
        except Exception:
            pass


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        _json_out({"ok": False, "error": f"invalid_input: {e}"})
        return

    try:
        result = asyncio.run(_run_with_sdk(payload))
        _json_out(result)
    except Exception as e:
        _json_out({"ok": False, "error": str(e)})


if __name__ == "__main__":
    main()
