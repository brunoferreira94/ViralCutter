import asyncio
import fnmatch
import json
import os
import sys


def _json_out(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


def _default_model_pool():
    # Contingência mínima caso models.list falhe.
    return [
        "claude*sonnet*",
        "gpt*",
        "gemini*",
        "raptor*",
    ]


def _build_model_pool():
    env_value = os.getenv("COPILOT_MODEL_POOL", "").strip()
    env_models = [item.strip() for item in env_value.split(",") if item.strip()] if env_value else []

    merged = []
    seen = set()
    for model in [*env_models, *_default_model_pool()]:
        lowered = model.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        merged.append(model)
    return merged


async def _list_available_models(client):
    try:
        models = await client.list_models()
        model_ids = []
        seen = set()
        for model in models or []:
            model_id = str(getattr(model, "id", "") or "").strip()
            if not model_id:
                continue
            lowered = model_id.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            model_ids.append(model_id)
        return model_ids
    except Exception:
        return []


def _match_from_pool(pattern, model_pool):
    pattern_lower = pattern.lower()
    return [m for m in model_pool if fnmatch.fnmatch(m.lower(), pattern_lower)]


def _fallback_candidates_for(requested_model, model_pool):
    requested_lower = requested_model.lower()

    fallback_patterns = []
    if "claude" in requested_lower and "sonnet" in requested_lower:
        fallback_patterns.extend(["claude*sonnet*", "claude*"])
    elif "claude" in requested_lower:
        fallback_patterns.append("claude*")

    fallback_patterns.extend(["gpt*", "gemini*", "raptor*"])

    ordered = []
    seen = set()
    for item in fallback_patterns:
        if "*" in item or "?" in item:
            candidates = _match_from_pool(item, model_pool)
        else:
            candidates = [item]

        for candidate in candidates:
            lowered = candidate.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            ordered.append(candidate)

    return ordered


async def _run_with_sdk(input_payload):
    from copilot import CopilotClient, SubprocessConfig
    from copilot.session import PermissionHandler

    prompt = str(input_payload.get("prompt", "")).strip()
    if not prompt:
        return {"ok": False, "error": "empty_prompt"}

    requested_model = str(input_payload.get("model", "gpt-5-mini")).strip() or "gpt-5-mini"
    github_token = str(input_payload.get("github_token", "")).strip()
    configured_model_pool = _build_model_pool()

    client_config = None
    if github_token:
        client_config = SubprocessConfig(
            github_token=github_token,
            use_logged_in_user=False,
        )

    client = CopilotClient(client_config)

    try:
        await client.start()
        available_models = await _list_available_models(client)
        model_pool = available_models if available_models else configured_model_pool
        model_candidates = []

        if "*" in requested_model or "?" in requested_model:
            model_candidates.extend(_match_from_pool(requested_model, model_pool))
        else:
            model_candidates.append(requested_model)

        model_candidates.extend(_fallback_candidates_for(requested_model, model_pool))

        # Remove duplicados preservando ordem.
        deduped_candidates = []
        seen = set()
        for candidate in model_candidates:
            lowered = candidate.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped_candidates.append(candidate)

        last_error = None
        for model_name in deduped_candidates:
            try:
                session = await client.create_session(
                    on_permission_request=PermissionHandler.approve_all,
                    model=model_name,
                    github_token=github_token or None,
                )
                response = await session.send_and_wait(prompt)

                content = ""
                if response is not None and getattr(response, "data", None) is not None:
                    content = getattr(response.data, "content", "") or ""

                return {
                    "ok": True,
                    "content": content,
                    "model_used": model_name,
                    "model_requested": requested_model,
                }
            except Exception as e:
                last_error = e
                continue

        return {
            "ok": False,
            "error": (
                f"No available model matched request '{requested_model}'. "
                f"Tried: {', '.join(deduped_candidates)}. "
                f"Last error: {last_error}"
            ),
        }
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
