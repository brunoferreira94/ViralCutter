import os
import json
import datetime
import uuid


def _default_folder(project_folder: str | None = None) -> str:
    if project_folder:
        return os.path.join(project_folder, "prompts")
    return os.path.join(os.getcwd(), "prompts_archive")


def save_prompt_response(prompt: str, response: str, provider: str = "unknown", model: str | None = None, project_folder: str | None = None) -> dict:
    """Save prompt and response to an organized folder and return file paths.

    Files created:
    - <folder>/<timestamp>_<id>_<provider>_prompt.txt
    - <folder>/<timestamp>_<id>_<provider>_response.txt
    - <folder>/<timestamp>_<id>_<provider>_meta.json
    """
    folder = _default_folder(project_folder)
    os.makedirs(folder, exist_ok=True)

    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    uid = uuid.uuid4().hex[:8]
    base = f"{ts}_{uid}_{provider}"

    prompt_path = os.path.join(folder, f"{base}_prompt.txt")
    response_path = os.path.join(folder, f"{base}_response.txt")
    meta_path = os.path.join(folder, f"{base}_meta.json")

    try:
        with open(prompt_path, "w", encoding="utf-8") as pf:
            pf.write(prompt or "")
    except Exception as e:
        return {"ok": False, "error": f"failed_write_prompt: {e}"}

    try:
        with open(response_path, "w", encoding="utf-8") as rf:
            rf.write(response or "")
    except Exception as e:
        return {"ok": False, "error": f"failed_write_response: {e}", "prompt_path": prompt_path}

    meta = {
        "timestamp": ts,
        "id": uid,
        "provider": provider,
        "model": model,
        "prompt_path": os.path.relpath(prompt_path),
        "response_path": os.path.relpath(response_path),
    }

    try:
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"ok": False, "error": f"failed_write_meta: {e}", "prompt_path": prompt_path, "response_path": response_path}

    return {"ok": True, "prompt_path": prompt_path, "response_path": response_path, "meta_path": meta_path}
