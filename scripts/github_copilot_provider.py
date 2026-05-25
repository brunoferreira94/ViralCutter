"""
GitHub Copilot SDK provider via dedicated local bridge process.

This provider keeps the rest of the ViralCutter pipeline synchronous while
delegating Copilot SDK session lifecycle/auth/message flow to
`scripts/copilot_sdk_bridge.py`.
"""

import json
import logging
import os
import subprocess
import sys
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    from . import prompt_store as _prompt_store
except Exception:
    try:
        import prompt_store as _prompt_store
    except Exception:
        _prompt_store = None


class GitHubCopilotProvider:
    def __init__(self, github_token: str, model: str = "gpt-4.1"):
        self.github_token = (github_token or "").strip()
        self.model = model or "gpt-4.1"
        self.bridge_timeout_sec = 240

    @property
    def bridge_path(self) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "copilot_sdk_bridge.py")

    def _call_bridge(self, prompt: str) -> str:
        payload = {
            "prompt": prompt,
            "model": self.model,
            "github_token": self.github_token,
        }

        proc = subprocess.run(
            [sys.executable, self.bridge_path],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=self.bridge_timeout_sec,
        )

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            raise RuntimeError(f"Copilot bridge exited with code {proc.returncode}: {stderr}")

        stdout = (proc.stdout or "").strip()
        if not stdout:
            raise RuntimeError("Copilot bridge returned empty output")

        try:
            result = json.loads(stdout)
        except Exception as e:
            raise RuntimeError(f"Copilot bridge returned invalid JSON: {e}. Raw: {stdout[:300]}")

        if not result.get("ok"):
            err = result.get("error", "unknown_error")
            raise RuntimeError(f"Copilot SDK error: {err}")

        used_model = str(result.get("model_used", "")).strip()
        if used_model and used_model != self.model:
            logger.info(
                "Copilot bridge resolved model '%s' -> '%s'",
                self.model,
                used_model,
            )
            self.model = used_model

        content = str(result.get("content", ""))

        # Best-effort: save prompt + response for organization
        try:
            if _prompt_store:
                try:
                    _prompt_store.save_prompt_response(prompt=prompt, response=content, provider="copilot", model=used_model)
                except Exception:
                    pass
        except Exception:
            pass

        return content

    def validate_token(self) -> bool:
        response = self._call_bridge("Reply with OK only.")
        return bool(response)

    def generate_segments(self, system_prompt: str, transcript: str, chunk_size: int = 10000) -> str:
        if not transcript or not transcript.strip():
            return json.dumps({"segments": []})

        # The upstream pipeline currently composes prompt+transcript into one prompt.
        prompt = transcript
        return self._call_bridge(prompt)


def create_copilot_provider(config: Dict) -> Optional[GitHubCopilotProvider]:
    github_token = str(config.get("github_token", "")).strip()
    model = str(config.get("model", "gpt-4.1")).strip() or "gpt-4.1"

    try:
        return GitHubCopilotProvider(github_token=github_token, model=model)
    except Exception as e:
        logger.warning(f"Invalid GitHub Copilot configuration: {e}")
        return None
