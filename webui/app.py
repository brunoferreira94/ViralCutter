# flake8: noqa
import gradio as gr  # type: ignore[reportMissingImports]
import subprocess
import os
import sys
import json
import psutil
import shutil
import datetime
import time
import webbrowser
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

import re
import library  # Module for Library Logic
import subtitle_handler as subs  # Module for Subtitles
import subtitle_editor as editor  # Module for Editor Logic
from scripts import copilot_oauth

# Path to the main script
MAIN_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main_improved.py"
)
WORKING_DIR = os.path.dirname(MAIN_SCRIPT_PATH)
sys.path.append(WORKING_DIR)

from config import COPILOT_MODELS, DEFAULT_COPILOT_MODEL, initialize_environment  # noqa: E402

from i18n.i18n import I18nAuto  # noqa: E402
i18n = I18nAuto()
APP_CONFIG = initialize_environment()

# --- PRESETS DEFINITIONS ---
FACE_PRESETS = {
    "Default (Balanced)": {"thresh": 0.35, "two_face": 0.60, "conf": 0.40, "dead_zone": 150},
    "Stable (Focus Main)": {"thresh": 0.60, "two_face": 0.80, "conf": 0.60, "dead_zone": 200},
    "Sensitive (Catch All)": {"thresh": 0.10, "two_face": 0.40, "conf": 0.30, "dead_zone": 100},
    "High Precision": {"thresh": 0.40, "two_face": 0.65, "conf": 0.75, "dead_zone": 150},
}

EXPERIMENTAL_PRESETS = {
    "Default (Off)": {"focus": False, "mar": 0.03, "score": 1.5, "motion": False, "motion_th": 3.0, "motion_sens": 0.05, "decay": 2.0},
    "Active Speaker (Balanced)": {"focus": True, "mar": 0.03, "score": 1.5, "motion": True, "motion_th": 3.0, "motion_sens": 0.05, "decay": 2.0},
    "Active Speaker (Sensitive)": {"focus": True, "mar": 0.02, "score": 1.0, "motion": True, "motion_th": 2.0, "motion_sens": 0.10, "decay": 1.0},
    "Active Speaker (Stable)": {"focus": True, "mar": 0.05, "score": 2.5, "motion": False, "motion_th": 5.0, "motion_sens": 0.02, "decay": 3.0},
}
# ---------------------------

VIRALS_DIR = os.path.join(WORKING_DIR, "VIRALS")
MODELS_DIR = os.path.join(WORKING_DIR, "models")

# Ensure directories exist
if not os.path.exists(VIRALS_DIR):
    os.makedirs(VIRALS_DIR, exist_ok=True)
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR, exist_ok=True)

# Global variables
current_process = None
copilot_oauth_pending = {}

DEBUG_COLORS_LOG = "debug_colors.log"
TEMP_SUBTITLE_CONFIG = "temp_subtitle_config.json"
SOURCE_YOUTUBE_URL = "YouTube URL"
SOURCE_EXISTING_PROJECT = "Existing Project"
SOURCE_UPLOAD_VIDEO = "Upload Video"
WORKFLOW_MAP = {"Full": "1", "Cut Only": "2", "Subtitles Only": "3"}  # NOSONAR
START_PROCESSING_LABEL = "Start Processing"
SELECT_PROJECT_LABEL = "Select Project"
API_KEY_LABEL = "API Key"
COPILOT_OAUTH_STATE_FILE = os.path.join(WORKING_DIR, "copilot_oauth_state.json")
PROVIDER_CONFIG_SAVED_MSG = "Provider configuration saved."

# Helpers
def _debug_color_log(message):
    try:
        with open(DEBUG_COLORS_LOG, "a", encoding="utf-8") as file_handle:
            file_handle.write(f"{message}\n")
    except OSError:
        pass


def _convert_rgb_to_ass(hex_clean, alpha):
    nums = re.findall(r"[\d\.]+", hex_clean)
    if len(nums) < 3:
        return None

    red = max(0, min(255, int(float(nums[0]))))
    green = max(0, min(255, int(float(nums[1]))))
    blue = max(0, min(255, int(float(nums[2]))))
    return f"&H{alpha}{blue:02X}{green:02X}{red:02X}&".upper()


def _convert_hex_to_ass(hex_clean, alpha):
    normalized = hex_clean
    if len(normalized) == 3:
        normalized = "".join([char * 2 for char in normalized])
    if len(normalized) != 6:
        return None

    red = normalized[0:2]
    green = normalized[2:4]
    blue = normalized[4:6]
    return f"&H{alpha}{blue}{green}{red}&".upper()


def convert_color_to_ass(hex_color, alpha="00"):
    _debug_color_log(f"INPUT: '{hex_color}'")
    if not hex_color:
        return f"&H{alpha}FFFFFF&"

    hex_clean = hex_color.lstrip("#").strip()
    if hex_clean.lower().startswith("rgb"):
        try:
            rgb_value = _convert_rgb_to_ass(hex_clean, alpha)
            if rgb_value:
                _debug_color_log(f"PARSED RGB: {rgb_value}")
                return rgb_value
        except ValueError as error:
            _debug_color_log(f"RGB ERROR: {error}")

    hex_value = _convert_hex_to_ass(hex_clean, alpha)
    if hex_value:
        _debug_color_log(f"PARSED HEX: {hex_value}")
        return hex_value

    _debug_color_log("INVALID: Defaulting to White")
    return f"&H{alpha}FFFFFF&"

def kill_process():
    global current_process
    if current_process:
        try:
            parent = psutil.Process(current_process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            current_process = None
            return i18n("Process terminated.")
        except Exception as e:
            return i18n("Error terminating process: {}").format(e)
    return i18n("No process running.")

GEMINI_MODELS = [
    'gemini-3-pro-preview',
    'gemini-2.5-flash',
    'gemini-2.5-flash-preview-09-2025',
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash-lite-preview-09-2025',
    'gemini-2.5-pro',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite'
]

G4F_MODELS = [
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4',
    'o1-mini',
    'o1',
    'deepseek-r1',
    'deepseek-v3',
    'llama-3.3-70b',
    'llama-3.1-405b',
    'claude-3.5-sonnet',
    'claude-3.7-sonnet',
    'gemini-2.0-flash',
    'qwen-2.5-72b'
]

def _resolve_provider_defaults(config):
    selected_api = config.get('selected_api', 'gemini')
    if selected_api == 'gemini':
        section = config.get('gemini', {})
        return (
            'gemini',
            i18n('Gemini API Key'),
            section.get('api_key', ''),
            GEMINI_MODELS,
            section.get('model', GEMINI_MODELS[1]),
            section.get('chunk_size', 70000),
        )
    if selected_api == 'copilot':
        section = config.get('copilot', {})
        return (
            'copilot',
            i18n('GitHub Token'),
            section.get('github_token', ''),
            COPILOT_MODELS,
            section.get('model', DEFAULT_COPILOT_MODEL),
            section.get('chunk_size', 10000),
        )
    if selected_api == 'g4f':
        section = config.get('g4f', {})
        return (
            'g4f',
            i18n(API_KEY_LABEL),
            '',
            G4F_MODELS,
            section.get('model', G4F_MODELS[5]),
            section.get('chunk_size', 70000),
        )
    if selected_api == 'local':
        section = config.get('local', {})
        local_models = get_local_models()
        model_choices = local_models if local_models else [i18n('No models found')]
        return (
            'local',
            i18n(API_KEY_LABEL),
            '',
            model_choices,
            section.get('model', model_choices[0]),
            section.get('chunk_size', 30000),
        )
    return ('manual', i18n(API_KEY_LABEL), '', [], '', 70000)

def get_local_models():
    if not os.path.exists(MODELS_DIR):
        return []
    return [f for f in os.listdir(MODELS_DIR) if f.endswith(".gguf")]


def get_api_config_path():
    return os.path.join(WORKING_DIR, "api_config.json")


def get_api_secrets_path():
    # Separate file for secrets (not committed)
    return os.path.join(WORKING_DIR, "api_secrets.json")


def load_api_config():
    config_path = get_api_config_path()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}

    # Load secrets overlay (tokens) from a local secrets file not tracked by git
    secrets_path = get_api_secrets_path()
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, 'r', encoding='utf-8') as sf:
                secrets = json.load(sf)
            # Merge secret fields into config (only for top-level sections)
            for section, values in secrets.items():
                if not isinstance(values, dict):
                    continue
                sec = config.setdefault(section, {})
                for k, v in values.items():
                    # Only override if value is truthy
                    if v:
                        sec[k] = v
        except Exception:
            pass

    return config


def save_api_config(selected_api, api_key, ai_model_name, chunk_size):
    config_path = get_api_config_path()
    config = load_api_config()
    config['selected_api'] = selected_api

    section_name_by_api = {
        'gemini': 'gemini',
        'copilot': 'copilot',
        'g4f': 'g4f',
        'local': 'local',
    }
    api_key_field_by_api = {
        'gemini': 'api_key',
        'copilot': 'github_token',
    }

    section_name = section_name_by_api.get(selected_api)
    if section_name:
        section = config.setdefault(section_name, {})
        key_field = api_key_field_by_api.get(selected_api)
        # Secrets (tokens) are stored in a separate local file to avoid committing them to git
        secrets_path = get_api_secrets_path()
        if key_field and api_key:
            # update in-memory config for immediate UI feedback, but persist token in secrets file
            section.pop(key_field, None)
            try:
                secrets = {}
                if os.path.exists(secrets_path):
                    with open(secrets_path, 'r', encoding='utf-8') as sf:
                        secrets = json.load(sf) or {}
                sec = secrets.setdefault(section_name, {})
                sec[key_field] = api_key
                with open(secrets_path, 'w', encoding='utf-8') as sf:
                    json.dump(secrets, sf, indent=4, ensure_ascii=False)
            except Exception:
                # fallback: keep in config file if secrets file cannot be written
                section[key_field] = api_key
        if ai_model_name:
            section['model'] = ai_model_name
        if chunk_size:
            section['chunk_size'] = int(chunk_size)

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return i18n(PROVIDER_CONFIG_SAVED_MSG)
    except Exception as e:
        return i18n("Error saving configuration: {} ").format(e)


def mask_secret(secret):
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def _persist_copilot_oauth_state(state):
    if not state:
        return
    payload = {
        "device_code": state.get("device_code", ""),
        "user_code": state.get("user_code", ""),
        "verification_uri": state.get("verification_uri", ""),
        "verification_uri_complete": state.get("verification_uri_complete", ""),
        "expires_in": int(state.get("expires_in", 0) or 0),
        "interval": int(state.get("interval", 0) or 0),
        "created_at": int(time.time()),
    }
    try:
        with open(COPILOT_OAUTH_STATE_FILE, "w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _clear_copilot_oauth_state():
    try:
        if os.path.exists(COPILOT_OAUTH_STATE_FILE):
            os.remove(COPILOT_OAUTH_STATE_FILE)
    except Exception:
        pass


def _load_copilot_oauth_state():
    if not os.path.exists(COPILOT_OAUTH_STATE_FILE):
        return {}

    try:
        with open(COPILOT_OAUTH_STATE_FILE, "r", encoding="utf-8") as file_handle:
            state = json.load(file_handle)
    except Exception:
        return {}

    created_at = int(state.get("created_at", 0) or 0)
    expires_in = int(state.get("expires_in", 0) or 0)
    if created_at and expires_in and int(time.time()) > (created_at + expires_in + 5):
        _clear_copilot_oauth_state()
        return {}

    if not state.get("device_code"):
        _clear_copilot_oauth_state()
        return {}

    return state


def open_github_token_page():
    return i18n("GitHub Copilot OAuth setup documentation opened in browser.")


def start_copilot_oauth_login(current_api_key):
    client_id = APP_CONFIG.copilot_oauth_client_id
    if not client_id:
        return current_api_key, i18n("Missing COPILOT_OAUTH_CLIENT_ID in environment (.env).")

    try:
        flow = copilot_oauth.start_device_flow(client_id=client_id)
        copilot_oauth_pending.clear()
        copilot_oauth_pending.update(flow)
        _persist_copilot_oauth_state(flow)

        verification_url = flow.get("verification_uri_complete") or flow.get("verification_uri", "")
        user_code = flow.get("user_code", "")
        expires_in = flow.get("expires_in", 0)

        if verification_url:
            try:
                webbrowser.open(verification_url)
            except Exception:
                pass

        return (
            current_api_key,
            i18n("Copilot OAuth started. Open: {} | Code: {} | Expires in: {}s. After authorizing, click Finish Copilot OAuth Login.")
            .format(verification_url, user_code, expires_in),
        )
    except Exception as e:
        return current_api_key, i18n("Unable to start Copilot OAuth flow: {} ").format(e)


def _handle_copilot_oauth_finish_error(current_api_key, error_code, error_description):
    if error_code == "authorization_pending":
        return current_api_key, i18n("OAuth authorization is still pending. Complete approval on GitHub and click Finish again.")
    if error_code == "slow_down":
        return current_api_key, i18n("OAuth requests are too frequent. Wait a few seconds and click Finish again.")
    if error_code == "expired_token":
        copilot_oauth_pending.clear()
        _clear_copilot_oauth_state()
        return current_api_key, i18n("OAuth device code expired. Click Start Copilot OAuth Login again.")
    return current_api_key, i18n("Unable to finish Copilot OAuth flow: {} - {} ").format(error_code, error_description)


def finish_copilot_oauth_login(current_api_key):
    client_id = APP_CONFIG.copilot_oauth_client_id
    client_secret = APP_CONFIG.copilot_oauth_client_secret
    if not client_id:
        return current_api_key, i18n("Missing COPILOT_OAUTH_CLIENT_ID in environment (.env).")

    if (not copilot_oauth_pending or not copilot_oauth_pending.get("device_code")):
        persisted_state = _load_copilot_oauth_state()
        if persisted_state:
            copilot_oauth_pending.clear()
            copilot_oauth_pending.update(persisted_state)

    if not copilot_oauth_pending or not copilot_oauth_pending.get("device_code"):
        return current_api_key, i18n("No active OAuth login session. Click Start Copilot OAuth Login first.")

    try:
        result = copilot_oauth.exchange_device_token(
            client_id=client_id,
            device_code=copilot_oauth_pending.get("device_code", ""),
            client_secret=client_secret,
        )

        if result.get("status") != "ok":
            error_code = result.get("error", "unknown_error")
            error_description = result.get("error_description", "")
            return _handle_copilot_oauth_finish_error(current_api_key, error_code, error_description)

        token = str(result.get("access_token", "")).strip()
        if not token:
            return current_api_key, i18n("OAuth finished without a valid token. Try again.")

        save_status = save_api_config("copilot", token, None, None)
        copilot_oauth_pending.clear()
        _clear_copilot_oauth_state()
        if PROVIDER_CONFIG_SAVED_MSG in save_status:
            return token, i18n("Copilot OAuth completed and token saved to secure local storage. {} ").format(mask_secret(token))
        return token, save_status
    except Exception as e:
        return current_api_key, i18n("Unexpected error finishing Copilot OAuth: {} ").format(e)


def start_github_cli_login():
    if not shutil.which("gh"):
        return i18n("GitHub CLI not found. Install gh to authenticate automatically.")

    try:
        if os.name == 'nt':
            command = 'start "GitHub Copilot Login" cmd /k gh auth login --web'
            subprocess.Popen(command, shell=True, cwd=WORKING_DIR)
        else:
            subprocess.Popen(["gh", "auth", "login", "--web"], cwd=WORKING_DIR)
        return i18n("GitHub CLI login started in a new terminal window.")
    except Exception as e:
        return i18n("Unable to start GitHub CLI login: {} ").format(e)


def import_github_cli_token():
    if not shutil.which("gh"):
        return i18n("GitHub CLI not found. Install gh to import a token automatically.")

    try:
        token = subprocess.check_output(["gh", "auth", "token"], stderr=subprocess.STDOUT, text=True).strip()
        if not token:
            return i18n("No token found in GitHub CLI. Run gh auth login --web first.")

        status = save_api_config("copilot", token, None, None)
        return i18n("GitHub token imported from GitHub CLI and saved. {} ").format(mask_secret(token)) if PROVIDER_CONFIG_SAVED_MSG in status else status
    except subprocess.CalledProcessError as e:
        output = e.output.strip() if hasattr(e, 'output') else str(e)
        return i18n("GitHub CLI error: {} ").format(output)
    except Exception as e:
        return i18n("Unexpected error importing GitHub token: {} ").format(e)


def apply_face_preset(preset_name):
    if preset_name not in FACE_PRESETS:
        return [gr.update() for _ in range(4)]  # No change

    p = FACE_PRESETS[preset_name]
    return p["thresh"], p["two_face"], p["conf"], p["dead_zone"]


def apply_experimental_preset(preset_name):
    if preset_name not in EXPERIMENTAL_PRESETS:
        return [gr.update() for _ in range(7)]  # No change

    p = EXPERIMENTAL_PRESETS[preset_name]
    return p["focus"], p["mar"], p["score"], p["motion"], p["motion_th"], p["motion_sens"], p["decay"]

# Subtitle logic moved to subtitle_handler.py


def run_viral_cutter(*args):  # NOSONAR
    (
        input_source, project_name, url, video_file, segments, viral, themes,
        min_duration, max_duration, model, ai_backend, api_key,
        ai_model_name, chunk_size, workflow, face_model, face_mode,
        face_detect_interval, no_face_mode, face_filter_thresh,
        face_two_thresh, face_conf_thresh, face_dead_zone,
        focus_active_speaker, active_speaker_mar, active_speaker_score_diff,
        include_motion, active_speaker_motion_threshold,
        active_speaker_motion_sensitivity, active_speaker_decay,
        use_custom_subs, font_name, font_size, font_color, highlight_color,
        outline_color, outline_thickness, shadow_color, shadow_size, is_bold,
        is_italic, is_uppercase, vertical_pos, alignment, h_size, w_block,
        gap, mode, under, strike, border_s, remove_punc, video_quality,
        use_youtube_subs, translate_target,
    ) = args

    global current_process
    yield "", gr.update(value=i18n("Running..."), interactive=False), gr.update(visible=True), None 
    logs = ""
    project_folder_path = None

    cmd = [sys.executable, MAIN_SCRIPT_PATH]
    
    # Input Source Logic
    if input_source == SOURCE_EXISTING_PROJECT:
        if not project_name:
             yield i18n("Error: No project selected."), gr.update(value=i18n(START_PROCESSING_LABEL), interactive=True), gr.update(visible=False), None
             return
        full_project_path = os.path.join(VIRALS_DIR, project_name)
        cmd.extend(["--project-path", full_project_path])
    elif input_source == SOURCE_UPLOAD_VIDEO:
        if not video_file:
             yield i18n("Error: No video file uploaded."), gr.update(value=i18n(START_PROCESSING_LABEL), interactive=True), gr.update(visible=False), None
             return
        
        # Determine project name from filename
        original_filename = os.path.basename(video_file)
        name_no_ext = os.path.splitext(original_filename)[0]
        # Sanitize: Allow alphanumeric, space, dash, underscore
        safe_name = "".join([c for c in name_no_ext if c.isalnum() or c in " _-"]).strip()
        if not safe_name: safe_name = "Untitled_Upload"
        
        # Always append timestamp as requested
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name_upload = f"{safe_name}_{timestamp}"
        project_path = os.path.join(VIRALS_DIR, project_name_upload)
             
        os.makedirs(project_path, exist_ok=True)
        
        target_path = os.path.join(project_path, "input.mp4")
        shutil.copy(video_file, target_path)
        
        cmd.extend(["--project-path", project_path])
        # Skip YouTube subs as it is a local upload
        cmd.append("--skip-youtube-subs")
        
    else:
        if url: cmd.extend(["--url", url])
        # Pass Video Quality
        if video_quality: cmd.extend(["--video-quality", video_quality])
        # Pass Subtitle Option (if False, we skip)
        if not use_youtube_subs: cmd.append("--skip-youtube-subs")
        
    # Translation
    if translate_target and translate_target != "None":
            cmd.extend(["--translate-target", translate_target])

    
    cmd.extend(["--segments", str(int(segments))])
    if viral: cmd.append("--viral")
    if themes: cmd.extend(["--themes", themes])
    cmd.extend(["--min-duration", str(int(min_duration))])
    cmd.extend(["--max-duration", str(int(max_duration))])
    cmd.extend(["--model", model])
    cmd.extend(["--ai-backend", ai_backend])
    if ai_backend in ["gemini", "copilot", "g4f", "local"]:
        save_api_config(ai_backend, api_key, ai_model_name, chunk_size)
    if api_key: cmd.extend(["--api-key", api_key])
    
    # New AI Params
    if ai_model_name: cmd.extend(["--ai-model-name", str(ai_model_name)])
    if chunk_size: cmd.extend(["--chunk-size", str(int(chunk_size))])

    cmd.extend(["--workflow", WORKFLOW_MAP.get(workflow, "1")])
    cmd.extend(["--face-model", face_model])
    cmd.extend(["--face-mode", face_mode])
    if face_detect_interval: cmd.extend(["--face-detect-interval", str(face_detect_interval)])
    if no_face_mode: cmd.extend(["--no-face-mode", no_face_mode])
    
    # New Face Params
    if face_filter_thresh is not None: cmd.extend(["--face-filter-threshold", str(face_filter_thresh)])
    if face_two_thresh is not None: cmd.extend(["--face-two-threshold", str(face_two_thresh)])
    if face_conf_thresh is not None: cmd.extend(["--face-confidence-threshold", str(face_conf_thresh)])
    if face_dead_zone is not None: cmd.extend(["--face-dead-zone", str(face_dead_zone)])


    
    cmd.append("--skip-prompts")
    
    if focus_active_speaker:
        cmd.append("--focus-active-speaker")
        if active_speaker_mar is not None: cmd.extend(["--active-speaker-mar", str(active_speaker_mar)])
        if active_speaker_score_diff is not None: cmd.extend(["--active-speaker-score-diff", str(active_speaker_score_diff)])
        if include_motion: cmd.append("--include-motion")
        if active_speaker_motion_threshold is not None: cmd.extend(["--active-speaker-motion-threshold", str(active_speaker_motion_threshold)])
        if active_speaker_motion_sensitivity is not None: cmd.extend(["--active-speaker-motion-sensitivity", str(active_speaker_motion_sensitivity)])
        if active_speaker_decay is not None: cmd.extend(["--active-speaker-decay", str(active_speaker_decay)])

    cmd.append("--skip-prompts") # Always skip prompts in WebUI to prevent freezing

    if use_custom_subs:
        subtitle_config = {
            "font": font_name, "base_size": int(font_size), "base_color": convert_color_to_ass(font_color), "highlight_color": convert_color_to_ass(highlight_color),
            "outline_color": convert_color_to_ass(outline_color), "outline_thickness": outline_thickness, "shadow_color": convert_color_to_ass(shadow_color),
            "shadow_size": shadow_size, "vertical_position": vertical_pos, "alignment": alignment, "bold": 1 if is_bold else 0, "italic": 1 if is_italic else 0, 
            "underline": 1 if under else 0, "strikeout": 1 if strike else 0, "border_style": border_s, "words_per_block": int(w_block), "gap_limit": gap,
            "mode": mode, "highlight_size": int(h_size), "remove_punctuation": remove_punc
        }
        # Uppercase is handled in main script or logic? 
        # Actually subtitle_config doesn't seem to natively support "uppercase" in get_subtitle_config default, but app.py was using it. 
        # I should probably add it back if I want to support it, but user said "PROHIBITED to remove existing ones".
        # I'll re-add 'uppercase': 1 if is_uppercase else 0 to the dict if the backend supports it, otherwise it's just ignored.
        # But wait, main_improved.py doesn't have 'uppercase' in get_subtitle_config. 
        # I'll keep it in the dict just in case logic uses it elsewhere or if I missed it.
        # Actually, standard ASS doesn't support uppercase flag directly in Style, it needs to be text transform.
        # But I'll leave it in the dict.
        subtitle_config["uppercase"] = 1 if is_uppercase else 0

        subtitle_config_path = os.path.join(WORKING_DIR, TEMP_SUBTITLE_CONFIG)
        try:
            with open(subtitle_config_path, "w", encoding="utf-8") as f:
                json.dump(subtitle_config, f, indent=4)
            cmd.extend(["--subtitle-config", subtitle_config_path])
        except Exception:
            pass
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    try:
        current_process = subprocess.Popen(cmd, cwd=WORKING_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, env=env)
        if input_source == SOURCE_EXISTING_PROJECT and project_name:
             # If using existing project, we already know the path, but let's see if logs confirm it
             project_folder_path = os.path.join(VIRALS_DIR, project_name)

        last_update_time = time.time()
        if current_process.stdout is None:
            raise RuntimeError("Unable to capture process stdout.")
        
        while True:
            line = current_process.stdout.readline()
            if not line and current_process.poll() is not None:
                break
            
            if line:
                logs += line
                if "Project Folder:" in line:
                    parts = line.split("Project Folder:")
                    if len(parts) > 1: project_folder_path = parts[1].strip()
                
                # Throttle updates to avoid browser freeze (0.2s interval)
                current_time = time.time()
                if current_time - last_update_time > 0.2:
                    yield logs, gr.update(visible=True, interactive=False), gr.update(visible=True), None
                    last_update_time = current_time
        
        # Final yield to ensure all logs are shown
        yield logs, gr.update(visible=True, interactive=False), gr.update(visible=True), None
    except Exception as e:
        logs += f"\nError running process: {str(e)}\n"
        yield logs, gr.update(visible=True, interactive=False), gr.update(visible=True), None
    finally:
        if current_process:
            if current_process.stdout:
                try:
                    current_process.stdout.close()
                except Exception:
                    pass
            if current_process.poll() is None:
                # If we are here, it means we finished reading or errored out, but process is still running.
                # If it was a normal break from loop, process should be done or close to done.
                # If we are stopping, current_process.terminate() might be needed outside? 
                # But here we just wait.
                try:
                    current_process.wait()
                except Exception:
                    pass
            current_process = None
    
    # Wait to ensure filesystem flush
    time.sleep(1.0)
    
    html_output = ""
    if project_folder_path and os.path.exists(project_folder_path):
        html_output = library.generate_project_gallery(project_folder_path, is_full_path=True)
    else:
        html_output = f"<h3>{i18n('Error: Project folder could not be determined from logs.')}</h3>"
    yield logs, gr.update(value=i18n(START_PROCESSING_LABEL), interactive=True), gr.update(visible=False), html_output

css = """
/* Global Dark Theme Overrides */
body, .gradio-container {
    background-color: #0b0b0b !important;
    color: #ffffff !important;
}

/* Force dark background for specific inputs that might be white */
input[type="password"], textarea, select {
    background-color: #1f1f1f !important;
    color: #ffffff !important;
    border: 1px solid #333 !important;
}

/* Hide Footer */
footer {visibility: hidden}

/* Container Width */
.gradio-container {
    max-width: 98% !important; 
    width: 98% !important;
    margin: 0 auto !important;
}
"""

api_cfg_defaults = _resolve_provider_defaults(load_api_config())
selected_api_default = api_cfg_defaults[0]
initial_api_label = api_cfg_defaults[1]
initial_api_key_value = api_cfg_defaults[2]
initial_model_choices = api_cfg_defaults[3]
initial_model_value = api_cfg_defaults[4]
initial_chunk = api_cfg_defaults[5]

import header

with gr.Blocks(title=i18n("ViralCutter WebUI"), theme=gr.themes.Default(primary_hue="orange", neutral_hue="slate"), css=css) as demo:
    gr.Markdown(header.badges)
    gr.Markdown(header.description)
    with gr.Tabs():
        with gr.Tab(i18n("Create New")):
             with gr.Row():
                with gr.Column(scale=1):
                    input_source = gr.Radio([(i18n(SOURCE_YOUTUBE_URL), SOURCE_YOUTUBE_URL), (i18n(SOURCE_EXISTING_PROJECT), SOURCE_EXISTING_PROJECT), (i18n(SOURCE_UPLOAD_VIDEO), SOURCE_UPLOAD_VIDEO)], label=i18n("Input Source"), value=SOURCE_YOUTUBE_URL)
                    
                    url_input = gr.Textbox(label=i18n(SOURCE_YOUTUBE_URL), placeholder="https://www.youtube.com/watch?v=...", visible=True)
                    video_upload = gr.File(label=i18n(SOURCE_UPLOAD_VIDEO), file_count="single", file_types=["video"], visible=False)
                    
                    with gr.Row():
                        video_quality_input = gr.Dropdown(choices=["best", "1080p", "720p", "480p"], label=i18n("Video Quality"), value="best")
                        translate_input = gr.Dropdown(choices=["None", "pt-BR", "pt", "en", "es", "fr", "de", "it", "ru", "ja", "ko", "zh-CN"], label=i18n("Translate Subtitles To"), value="pt-BR")
                        use_youtube_subs_input = gr.Checkbox(label=i18n("Use YouTube Subs"), value=True, info=i18n("Download and use official subtitles if available. (Recommended, it speeds up the process)"))

                    project_selector = gr.Dropdown(choices=[], label=i18n(SELECT_PROJECT_LABEL), visible=False)
                    
                    def on_source_change(source):
                        if source == SOURCE_YOUTUBE_URL:
                            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(value="Full") 
                        elif source == SOURCE_UPLOAD_VIDEO:
                             return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(value="Full")
                        else:
                            # Load projects
                            projs = library.get_existing_projects()
                            return gr.update(visible=False), gr.update(choices=projs, visible=True), gr.update(visible=False), gr.update(value="Subtitles Only")
                    
                    
                    with gr.Row():
                        segments_input = gr.Number(label=i18n("Segments"), value=3, precision=0)
                        viral_input = gr.Checkbox(label=i18n("Viral Mode"), value=True)
                    themes_input = gr.Textbox(label=i18n("Themes"), placeholder=i18n("funny, sad..."), visible=False)
                    viral_input.change(lambda x: gr.update(visible=not x), viral_input, themes_input)
                    with gr.Row():
                        min_dur_input = gr.Number(label=i18n("Min Duration (s)"), value=15)
                        max_dur_input = gr.Number(label=i18n("Max Duration (s)"), value=90)
                with gr.Column(scale=1):
                    with gr.Row():
                        ai_backend_input = gr.Dropdown(choices=[(i18n("Gemini"), "gemini"), (i18n("G4F"), "g4f"), (i18n("GitHub Copilot"), "copilot"), (i18n("Local (GGUF)"), "local"), (i18n("Manual"), "manual")], label=i18n("AI Backend"), value=selected_api_default, scale=2)
                        api_key_input = gr.Textbox(label=initial_api_label, type="password", value=initial_api_key_value, scale=3)
                    
                    # New Dynamic Inputs
                    with gr.Row():
                        ai_model_input = gr.Dropdown(choices=initial_model_choices, label=i18n("AI Model"), value=initial_model_value, allow_custom_value=True, visible=(selected_api_default != "manual"), scale=5)
                        refresh_models_btn = gr.Button("🔄", size="sm", visible=False, scale=0, min_width=50) # Only local
                        save_config_btn = gr.Button(i18n("Save Provider Config"), size="sm", scale=0, min_width=120)
                        chunk_size_input = gr.Number(label=i18n("Chunk Size"), value=initial_chunk, precision=0, scale=2)
                        config_status_output = gr.Textbox(label=i18n("Config Status"), value="", interactive=False, lines=1)

                    with gr.Row():
                        start_copilot_oauth_btn = gr.Button(i18n("Start Copilot OAuth Login"), size="sm", scale=0, min_width=180)
                        finish_copilot_oauth_btn = gr.Button(i18n("Finish Copilot OAuth Login"), size="sm", scale=0, min_width=180)
                        login_gh_cli_btn = gr.Button(i18n("Login with GitHub CLI"), size="sm", scale=0, min_width=180)
                        import_gh_cli_btn = gr.Button(i18n("Import Token from GitHub CLI"), size="sm", scale=0, min_width=220)

                    # Update listeners with logic to hide/show API key
                    def update_ai_ui(backend):
                        show_api = (backend in ["gemini", "copilot"])
                        show_refresh = (backend == "local")
                        
                        # Update API key label based on backend
                        if backend == "gemini":
                            api_label = i18n("Gemini API Key")
                        elif backend == "copilot":
                            api_label = i18n("GitHub Token")
                        else:
                            api_label = i18n("API Key")
                        
                        # Definições padrão para evitar que fiquem vazios
                        new_choices = []
                        new_val = ""
                        new_chunk = 70000
                        
                        if backend == "gemini":
                            new_choices = GEMINI_MODELS
                            new_val = GEMINI_MODELS[1]
                            new_chunk = 70000
                        elif backend == "g4f":
                            new_choices = G4F_MODELS
                            new_val = G4F_MODELS[5]
                            new_chunk = 70000
                        elif backend == "copilot":
                            new_choices = COPILOT_MODELS
                            new_val = DEFAULT_COPILOT_MODEL
                            new_chunk = 10000
                        elif backend == "local":
                            models = get_local_models()
                            new_choices = models if models else [i18n("No models found")]
                            new_val = new_choices[0]
                            new_chunk = 30000
                        else: # Manual
                             pass

                        return (
                            gr.update(visible=show_api, label=api_label), # API Key Visibility & Label
                            gr.update(choices=new_choices, value=new_val, visible=(backend != "manual")), # Model Dropdown
                            gr.update(visible=show_refresh), # Refresh Button
                            gr.update(value=new_chunk) # Chunk Size
                        )

                    def refresh_local_models():
                        models = get_local_models()
                        val = models[0] if models else i18n("No models found")
                        return gr.update(choices=models, value=val)

                    refresh_models_btn.click(refresh_local_models, outputs=ai_model_input)
                    save_config_btn.click(save_api_config, inputs=[ai_backend_input, api_key_input, ai_model_input, chunk_size_input], outputs=[config_status_output])
                    start_copilot_oauth_btn.click(
                        start_copilot_oauth_login,
                        inputs=[api_key_input],
                        outputs=[api_key_input, config_status_output],
                    )
                    finish_copilot_oauth_btn.click(
                        finish_copilot_oauth_login,
                        inputs=[api_key_input],
                        outputs=[api_key_input, config_status_output],
                    )
                    login_gh_cli_btn.click(start_github_cli_login, outputs=[config_status_output])
                    import_gh_cli_btn.click(import_github_cli_token, outputs=[config_status_output])
                    ai_backend_input.change(update_ai_ui, inputs=ai_backend_input, outputs=[api_key_input, ai_model_input, refresh_models_btn, chunk_size_input])

                    model_input = gr.Dropdown(["tiny", "small", "medium", "large", "large-v1", "large-v2", "large-v3", "turbo", "large-v3-turbo", "distil-large-v2", "distil-medium.en", "distil-small.en", "distil-large-v3"], label=i18n("Whisper Model"), value="large-v3-turbo")
                    with gr.Row():
                        workflow_input = gr.Dropdown(choices=[(i18n("Full"), "Full"), (i18n("Cut Only"), "Cut Only"), (i18n("Subtitles Only"), "Subtitles Only")], label=i18n("Workflow"), value="Full")
                        face_model_input = gr.Dropdown(["insightface", "mediapipe"], label=i18n("Face Model"), value="insightface")
                    with gr.Row():
                        face_mode_input = gr.Dropdown(choices=[(i18n("Auto"), "auto"), ("1", "1"), ("2", "2")], label=i18n("Face Mode"), value="auto")
                        face_detect_interval_input = gr.Textbox(label=i18n("Face Det. Interval"), value="0.17,1.0")
                        no_face_mode_input = gr.Dropdown(choices=[(i18n("Padding (9:16)"), "padding"), (i18n("Zoom (Center)"), "zoom")], label=i18n("No Face Fallback"), value="zoom")
                    
                    
                    # Update listeners now that all components are defined
                    input_source.change(on_source_change, inputs=input_source, outputs=[url_input, project_selector, video_upload, workflow_input])
             
             with gr.Accordion(i18n("Advanced Face Settings"), open=False):
                 face_preset_input = gr.Dropdown(choices=[(i18n(k), k) for k in FACE_PRESETS.keys()], label=i18n("Configuration Presets"), value="Default (Balanced)", interactive=True)
                 with gr.Row():
                      face_filter_thresh_input = gr.Slider(label=i18n("Ignore Small Faces (0.0 - 1.0)"), minimum=0.0, maximum=1.0, value=0.35, step=0.05, info=i18n("Relative size to ignore background."))
                      face_two_thresh_input = gr.Slider(label=i18n("Threshold for 2 Faces (0.0 - 1.0)"), minimum=0.0, maximum=1.0, value=0.60, step=0.05, info=i18n("Size of 2nd face to activate split mode."))
                      face_conf_thresh_input = gr.Slider(label=i18n("Minimum Confidence (0.0 - 1.0)"), minimum=0.0, maximum=1.0, value=0.40, step=0.05, info=i18n("Ignore detections with low confidence."))
                      face_dead_zone_input = gr.Slider(label=i18n("Dead Zone (Stabilization)"), minimum=0, maximum=200, value=150, step=5, info=i18n("Movement pixels to ignore."))
                 
                 face_preset_input.change(apply_face_preset, inputs=face_preset_input, outputs=[face_filter_thresh_input, face_two_thresh_input, face_conf_thresh_input, face_dead_zone_input])

                 with gr.Accordion(i18n("Experimental: Active Speaker & Motion"), open=False):
                        experimental_preset_input = gr.Dropdown(choices=[(i18n(k), k) for k in EXPERIMENTAL_PRESETS.keys()], label=i18n("Configuration Presets"), value="Default (Off)", interactive=True)
                        focus_active_speaker_input = gr.Checkbox(label=i18n("Experimental: Focus on Speaker"), value=False, info=i18n("Tries to focus only on the speaking person instead of split screen."))
                        with gr.Row():
                            active_speaker_mar_input = gr.Slider(label=i18n("MAR Threshold (Mouth Open)"), minimum=0.01, maximum=0.20, value=0.03, step=0.005, info=i18n("Mouth open sensitivity."))
                            active_speaker_score_diff_input = gr.Slider(label=i18n("Score Difference"), minimum=0.5, maximum=10.0, value=1.5, step=0.5, info=i18n("Minimum difference to focus on 1 face."))
                            
                        with gr.Row():
                            include_motion_input = gr.Checkbox(label=i18n("Consider Motion"), value=False, info=i18n("Increases score with motion (gestures)."))
                            
                        with gr.Row():
                            active_speaker_motion_threshold_input = gr.Slider(label=i18n("Motion Dead Zone"), minimum=0.0, maximum=20.0, value=3.0, step=0.5, info=i18n("Pixels ignored."))
                            active_speaker_motion_sensitivity_input = gr.Slider(label=i18n("Motion Sensitivity"), minimum=0.01, maximum=0.5, value=0.05, step=0.01, info=i18n("Points per pixel."))
                            active_speaker_decay_input = gr.Slider(label=i18n("Switch Speed"), minimum=0.5, maximum=5.0, value=2.0, step=0.5, info=i18n("Speed to lose focus."))

                        experimental_preset_input.change(apply_experimental_preset, inputs=experimental_preset_input, outputs=[focus_active_speaker_input, active_speaker_mar_input, active_speaker_score_diff_input, include_motion_input, active_speaker_motion_threshold_input, active_speaker_motion_sensitivity_input, active_speaker_decay_input])
             with gr.Accordion(i18n("Subtitle Settings (alpha)"), open=False):
                preset_input = gr.Dropdown(choices=[(i18n("Manual"), "Manual")] + [(i18n(k), k) for k in subs.SUBTITLE_PRESETS.keys()], label=i18n("Quick Presets"), value="Hormozi (Classic)")
                use_custom_subs = gr.Checkbox(label=i18n("Enable Subtitle Customization (Includes Preset)"), value=True)
                
                # Previews (Always Visible)
                preview_html = gr.HTML(value=f"<div style='text-align:center; padding:10px; color:#666;'>{i18n('Select options or preset to preview')}</div>")
                
                with gr.Row():
                    preview_vid_btn = gr.Button(i18n("🎬 Render Animated Preview (Slow)"), size="sm")
                preview_vid = gr.Video(label=i18n("Animated Preview"), height=300, autoplay=True, interactive=False)
                
                with gr.Accordion(i18n("Advanced Settings"), open=False):
                    gr.Markdown(f"### {i18n('Appearance')}")
                    with gr.Row():
                        font_name_input = gr.Textbox(label=i18n("Font Name"), value="Montserrat-Regular")
                        font_size_input = gr.Slider(label=i18n("Font Size (Base)"), minimum=8, maximum=80, value=12)
                        highlight_size_input = gr.Slider(label=i18n("Highlight Size"), minimum=8, maximum=80, value=14)
                    
                    with gr.Row():
                        font_color_input = gr.ColorPicker(label=i18n("Base Color"), value="#FFFFFF")
                        highlight_color_input = gr.ColorPicker(label=i18n("Highlight Color"), value="#00FF00")
                        outline_color_input = gr.ColorPicker(label=i18n("Outline Color"), value="#000000")
                        shadow_color_input = gr.ColorPicker(label=i18n("Shadow Color"), value="#000000")
                    
                    gr.Markdown(f"### {i18n('Styling & Effects')}")
                    with gr.Row():
                        outline_thickness_input = gr.Slider(label=i18n("Outline Thickness"), minimum=0, maximum=10, value=1.5)
                        shadow_size_input = gr.Slider(label=i18n("Shadow Size"), minimum=0, maximum=10, value=2)
                        border_style_input = gr.Dropdown(choices=[(i18n("Outline"), 1), (i18n("Opaque Box"), 3)], label=i18n("Border Style"), value=1)
                    
                    with gr.Row():
                        bold_input = gr.Checkbox(label=i18n("Bold"))
                        italic_input = gr.Checkbox(label=i18n("Italic"))
                        uppercase_input = gr.Checkbox(label=i18n("Uppercase"))
                        remove_punc_input = gr.Checkbox(label=i18n("Remove Punctuation"), value=True)
                        underline_input = gr.Checkbox(label=i18n("Underline"))
                        strikeout_input = gr.Checkbox(label=i18n("Strikeout"))
                        
                    gr.Markdown(f"### {i18n('Positioning & Layout')}")
                    with gr.Row():
                        vertical_pos_input = gr.Slider(label=i18n("V-Pos (Margin V)"), minimum=0, maximum=500, value=210)
                        alignment_input = gr.Dropdown(choices=[(i18n("Left"), 1), (i18n("Center"), 2), (i18n("Right"), 3)], label=i18n("Alignment"), value=2)
                        gap_limit_input = gr.Slider(label=i18n("Gap Limit"), minimum=0.0, maximum=5.0, value=0.5, step=0.1)
                        mode_input = gr.Dropdown(choices=[(i18n("Highlight"), "highlight"), (i18n("Word by Word"), "word_by_word"), (i18n("No Highlight"), "no_highlight")], label=i18n("Mode"), value="highlight")
                        words_per_block_input = gr.Slider(label=i18n("Words per Block"), minimum=1, maximum=20, value=3, step=1)

                manual_inputs = [
                    font_name_input, font_size_input, font_color_input, highlight_color_input, 
                    outline_color_input, outline_thickness_input, shadow_color_input, shadow_size_input, 
                    bold_input, italic_input, uppercase_input,
                    highlight_size_input, words_per_block_input, gap_limit_input, mode_input,
                    underline_input, strikeout_input, border_style_input,
                    vertical_pos_input, alignment_input,
                    remove_punc_input
                ]
                
                # Update manual inputs when preset changes
                preset_input.change(subs.apply_preset, inputs=[preset_input], outputs=manual_inputs)
                
                # Auto-update PREVIEW HTML on any change
                for inp in manual_inputs:
                    inp.change(subs.generate_preview_html, inputs=manual_inputs, outputs=preview_html)
                
                # Render video button
                preview_vid_btn.click(
                    subs.render_preview_video,
                    inputs=manual_inputs,
                    outputs=preview_vid
                )
                
                # Initial load
                demo.load(subs.generate_preview_html, inputs=manual_inputs, outputs=preview_html)
                demo.load(subs.apply_preset, inputs=[preset_input], outputs=manual_inputs) # Apply default preset on load

             with gr.Row():
                 start_btn = gr.Button(i18n(START_PROCESSING_LABEL), variant="primary")
                 stop_btn = gr.Button(i18n("Stop"), variant="stop", visible=False)
             stop_btn.click(kill_process, outputs=[])
             logs_output = gr.Textbox(label=i18n("Logs"), lines=10, autoscroll=True, elem_id="logs_output")
             
             # Force scroll to bottom via JS
             logs_output.change(fn=None, inputs=[], outputs=[], js="""
                function() {
                    var ta = document.querySelector('#logs_output textarea');
                    if(ta) {
                        // Setup scroll listener once to track user intent
                        if (!ta._scrollerSetup) {
                            ta._isSticky = true; // Default to sticky
                            ta.addEventListener('scroll', function() {
                                var diff = ta.scrollHeight - ta.scrollTop - ta.clientHeight;
                                // If near bottom (<50px), enable sticky. Else disable.
                                if (diff <= 50) {
                                     ta._isSticky = true;
                                } else {
                                     ta._isSticky = false;
                                }
                            });
                            ta._scrollerSetup = true;
                        }
                        
                        // Apply scroll only if sticky
                        if(ta._isSticky === undefined || ta._isSticky === true) {
                            ta.scrollTop = ta.scrollHeight;
                        }
                    }
                }
             """)
             results_html = gr.HTML(label=i18n("Results"))
             
             # MUST pass all all new inputs to the run function
             start_btn.click(run_viral_cutter, inputs=[
                 input_source, project_selector, url_input, video_upload, segments_input, viral_input, themes_input, min_dur_input, max_dur_input, 
                 model_input, ai_backend_input, api_key_input, ai_model_input, chunk_size_input, 
                 workflow_input, face_model_input, face_mode_input, face_detect_interval_input, no_face_mode_input, 
                 face_filter_thresh_input, face_two_thresh_input, face_conf_thresh_input, face_dead_zone_input, focus_active_speaker_input, 
                 active_speaker_mar_input, active_speaker_score_diff_input, include_motion_input, active_speaker_motion_threshold_input, active_speaker_motion_sensitivity_input, active_speaker_decay_input,
                 use_custom_subs, 
                 # Expanded Manual Inputs mapping
                 font_name_input, font_size_input, font_color_input, highlight_color_input, 
                 outline_color_input, outline_thickness_input, shadow_color_input, shadow_size_input, 
                 bold_input, italic_input, uppercase_input, vertical_pos_input, alignment_input,
                 # New Inputs
                 highlight_size_input, words_per_block_input, gap_limit_input, mode_input, 
                 underline_input, strikeout_input, border_style_input, remove_punc_input,
                 video_quality_input, use_youtube_subs_input, translate_input
             ], outputs=[logs_output, start_btn, stop_btn, results_html])


        with gr.Tab(i18n("Subtitle Editor")):
            gr.Markdown(f"### {i18n('Edit Subtitles (Smart Mode)')}")
            
            with gr.Group():
                editor_project_dropdown = gr.Dropdown(choices=library.get_existing_projects(), label=i18n(SELECT_PROJECT_LABEL), value=None)
                editor_refresh_btn = gr.Button(i18n("Refresh"), size="sm")
            
            with gr.Group():
                editor_file_dropdown = gr.Dropdown(choices=[], label=i18n("Select Subtitle File"), interactive=True)
                editor_load_btn = gr.Button(i18n("Load Subtitles"), variant="secondary")

            # Hidden state to store full path of currently loaded JSON
            current_json_path = gr.State()

            # The Dataframe Editor
            # Headers: Start, End, Text
            subtitle_dataframe = gr.Dataframe(
                headers=["Start", "End", "Text"],
                datatype=["str", "str", "str"],
                col_count=(3, "fixed"),
                interactive=True,
                label=i18n("Subtitle Segments"),
                wrap=True
            )

            with gr.Row():
                editor_save_btn = gr.Button(i18n("💾 Save Changes"), variant="primary")
                editor_render_single_btn = gr.Button(i18n("⚡ Render This Segment (Very-Fast)"), variant="secondary")
                editor_render_all_btn = gr.Button(i18n("🎬 Render All (Fast)"), variant="stop")
            
            editor_status = gr.Textbox(label=i18n("Status"), interactive=False)

            # --- Callbacks for Editor ---
            editor_refresh_btn.click(library.refresh_projects, outputs=editor_project_dropdown)

            def update_file_list(proj_name):
                if not proj_name: return gr.update(choices=[])
                proj_path = os.path.join(VIRALS_DIR, proj_name)
                files = editor.list_editable_files(proj_path)
                return gr.update(choices=files, value=files[0] if files else None)

            editor_project_dropdown.change(update_file_list, inputs=editor_project_dropdown, outputs=editor_file_dropdown)

            def load_subs(proj_name, file_name):
                if not proj_name or not file_name:
                    return [], None, i18n("Please select project and file.")
                
                full_path = os.path.join(VIRALS_DIR, proj_name, 'subs', file_name)
                data = editor.load_transcription_for_editor(full_path)
                return data, full_path, i18n("Loaded {} segments.").format(len(data))

            editor_load_btn.click(load_subs, inputs=[editor_project_dropdown, editor_file_dropdown], outputs=[subtitle_dataframe, current_json_path, editor_status])

            def save_subs(json_path, df):
                if not json_path: return i18n("No file loaded.")
                data_list = df.values.tolist() if hasattr(df, 'values') else df
                msg = editor.save_editor_changes(json_path, data_list)
                return msg

            editor_save_btn.click(save_subs, inputs=[current_json_path, subtitle_dataframe], outputs=editor_status)

            def render_single(*single_args):  # NOSONAR
                (
                    json_path, use_custom, font_name, font_size, font_color,
                    highlight_color, outline_color, outline_thickness,
                    shadow_color, shadow_size, is_bold, is_italic,
                    is_uppercase, h_size, w_block, gap, mode, under, strike,
                    border_s, vertical_pos, alignment, remove_punc,
                ) = single_args

                if not json_path:
                    return i18n("No file loaded.")
                
                subtitle_config_path = os.path.join(WORKING_DIR, TEMP_SUBTITLE_CONFIG)
                
                # Save config if custom subs enabled
                if use_custom:
                    subtitle_config = {
                        "font": font_name, "base_size": int(font_size), 
                        "base_color": convert_color_to_ass(font_color), 
                        "highlight_color": convert_color_to_ass(highlight_color),
                        "outline_color": convert_color_to_ass(outline_color), 
                        "outline_thickness": outline_thickness, 
                        "shadow_color": convert_color_to_ass(shadow_color),
                        "shadow_size": shadow_size, "vertical_position": vertical_pos, 
                        "alignment": alignment, "bold": 1 if is_bold else 0, 
                        "italic": 1 if is_italic else 0, 
                        "underline": 1 if under else 0, "strikeout": 1 if strike else 0, 
                        "border_style": border_s, "words_per_block": int(w_block), 
                        "gap_limit": gap, "mode": mode, "highlight_size": int(h_size),
                        "uppercase": 1 if is_uppercase else 0,
                        "remove_punctuation": remove_punc
                    }
                    try:
                        with open(subtitle_config_path, "w", encoding="utf-8") as f:
                            json.dump(subtitle_config, f, indent=4)
                    except Exception:
                        pass
                else:
                    # Remove temp config if it exists to ensure defaults are used
                    try:
                        if os.path.exists(subtitle_config_path):
                            os.remove(subtitle_config_path)
                    except Exception:
                        pass
                
                # We expect user to SAVE first, but we could auto-save.
                # For now assume saved.
                msg = editor.render_specific_video(json_path)
                return msg

            editor_render_single_btn.click(
                render_single, 
                inputs=[current_json_path, use_custom_subs] + manual_inputs, 
                outputs=editor_status
            )

            def render_all(*all_args):  # NOSONAR
                (
                    proj_name, use_custom, font_name, font_size, font_color,
                    highlight_color, outline_color, outline_thickness,
                    shadow_color, shadow_size, is_bold, is_italic,
                    is_uppercase, h_size, w_block, gap, mode, under, strike,
                    border_s, vertical_pos, alignment, remove_punc,
                ) = all_args
                if not proj_name:
                    return i18n("No project selected.")
                
                # Save config
                if use_custom:
                    subtitle_config = {
                        "font": font_name, "base_size": int(font_size), 
                        "base_color": convert_color_to_ass(font_color), 
                        "highlight_color": convert_color_to_ass(highlight_color),
                        "outline_color": convert_color_to_ass(outline_color), 
                        "outline_thickness": outline_thickness, 
                        "shadow_color": convert_color_to_ass(shadow_color),
                        "shadow_size": shadow_size, "vertical_position": vertical_pos, 
                        "alignment": alignment, "bold": 1 if is_bold else 0, 
                        "italic": 1 if is_italic else 0, 
                        "underline": 1 if under else 0, "strikeout": 1 if strike else 0, 
                        "border_style": border_s, "words_per_block": int(w_block), 
                        "gap_limit": gap, "mode": mode, "highlight_size": int(h_size),
                        "uppercase": 1 if is_uppercase else 0,
                        "remove_punctuation": remove_punc
                    }
                    subtitle_config_path = os.path.join(WORKING_DIR, TEMP_SUBTITLE_CONFIG)
                    try:
                        with open(subtitle_config_path, "w", encoding="utf-8") as f:
                            json.dump(subtitle_config, f, indent=4)
                    except Exception:
                        pass

                proj_path = os.path.join(VIRALS_DIR, proj_name)
                
                # IMPORTANT: Pass the config file path to the command
                subtitle_config_path = os.path.join(WORKING_DIR, TEMP_SUBTITLE_CONFIG)
                cmd = [sys.executable, MAIN_SCRIPT_PATH, "--project-path", proj_path, "--workflow", "3", "--skip-prompts"]
                
                if use_custom and os.path.exists(subtitle_config_path):
                     cmd.extend(["--subtitle-config", subtitle_config_path])

                try:
                    subprocess.Popen(cmd, cwd=WORKING_DIR)
                    return i18n("Render All started in background... Check terminal/logs.")
                except Exception as e:
                    return i18n("Error starting render: {}").format(e)

            editor_render_all_btn.click(
                render_all, 
                inputs=[editor_project_dropdown, use_custom_subs] + manual_inputs, 
                outputs=editor_status
            )


        with gr.Tab(i18n("Library")):
            gr.Markdown(f"### {i18n('Existing Projects')}")
            with gr.Row():
                project_dropdown = gr.Dropdown(choices=library.get_existing_projects(), label=i18n("Select Project"), value=None)
                refresh_btn = gr.Button(i18n("Refresh List"))
            project_gallery_html = gr.HTML()
            refresh_btn.click(library.refresh_projects, outputs=project_dropdown)
            def on_select_project(proj_name): return library.generate_project_gallery(proj_name)
            project_dropdown.change(on_select_project, project_dropdown, project_gallery_html)
    
    gr.Markdown(f"""
        <hr>
        <div style='text-align: center; font-size: 0.9em; color: #777;'>
            <p>
                <strong>{i18n('Desenvolvido por Rafael Godoy')}</strong>
                <br>
                {i18n('Apoie o projeto, qualquer valor é bem-vindo:')} 
                <a href='https://nubank.com.br/pagar/1ls6a4/0QpSSbWBSq' target='_blank'><strong>{i18n('Apoiar via PIX')}</strong></a>
                <br>
                {i18n('100% local • open source • no subscription required')} 
            </p>
        </div>
        """)
if __name__ == "__main__":
    import webbrowser
    import threading
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--colab", action="store_true", help="Run in Google Colab mode")
    args = parser.parse_args()

    if args.colab:
        print("Running in Colab mode. Generating public link with Static Mounts...")
        library.set_url_mode("fastapi")
        
        # Broaden allowed paths for Colab
        allowed_dirs = [VIRALS_DIR, WORKING_DIR, os.getcwd(), "."]
        
        # Explicitly set static paths
        try:
            gr.set_static_paths(paths=allowed_dirs)
            print(f"DEBUG: Registered static paths: {allowed_dirs}")
        except AttributeError:
            print("DEBUG: gr.set_static_paths not available")
        
        print(f"DEBUG: Allowed paths for Gradio: {allowed_dirs}")
        
        # Launch with prevent_thread_lock to allow mounting
        app, local_url, share_url = demo.queue().launch(
            share=True, 
            allowed_paths=allowed_dirs,
            prevent_thread_lock=True
        )
        
        # Mount the VIRALS directory explicitly
        app.mount("/virals", StaticFiles(directory=VIRALS_DIR), name="virals")
        print(f"Mounted /virals to {VIRALS_DIR}")
        
        demo.block_thread()
    else:
        # Check environment
        is_windows = (os.name == 'nt')
        
        library.set_url_mode("fastapi")
        allowed_dirs = [VIRALS_DIR, WORKING_DIR, os.getcwd(), "."]
        try:
            gr.set_static_paths(paths=allowed_dirs)
        except AttributeError: pass
        
        from fastapi.responses import FileResponse
        from fastapi import BackgroundTasks

        # Helper to attach routes to any FastAPI app (whether created by Gradio or us)
        def attach_extra_routes(fastapi_app):
            fastapi_app.mount("/virals", StaticFiles(directory=VIRALS_DIR), name="virals")
            
            @fastapi_app.get("/export_xml_api")
            def export_xml_api(project: str, segment: int, background_tasks: BackgroundTasks, format: str = "premiere"):
                try:
                    project_path = os.path.join(VIRALS_DIR, project)
                    script_path = os.path.join(WORKING_DIR, "scripts", "export_xml.py")
                    cmd = [sys.executable, script_path, "--project", project_path, "--segment", str(segment), "--format", format]
                    subprocess.run(cmd, check=True)
                    proj_name = os.path.basename(project_path)
                    zip_filename = f"export_{proj_name}_seg{segment}.zip"
                    file_path = os.path.join(project_path, zip_filename)
                    if os.path.exists(file_path):
                        return FileResponse(file_path, filename=zip_filename, media_type='application/zip')
                    else:
                        return {"error": f"File generation failed. Expected: {file_path}"}
                except Exception as e:
                    return {"error": str(e)}
            
            print(f"Mounted /virals to {VIRALS_DIR}")

        if is_windows:
            print("Running in Windows environment (using Gradio launch for convenience).")
            # Windows: Use demo.launch() for convenience (auto-browser, etc)
            app, local_url, share_url = demo.queue().launch(
                share=False, 
                allowed_paths=allowed_dirs, 
                inbrowser=True,
                server_name=APP_CONFIG.viralcutter_host,
                server_port=7860,
                prevent_thread_lock=True
            )
            attach_extra_routes(app)
            demo.block_thread()
        else:
            print("Running in Linux/Container environment (using Uvicorn for stability).")
            # Linux/HF: Use Uvicorn for explicit loop control
            app = FastAPI()
            attach_extra_routes(app)
            # Disable SSR to prevent Node proxying issues on HF Spaces
            app = gr.mount_gradio_app(app, demo.queue(), path="/", allowed_paths=allowed_dirs, ssr_mode=False)
            uvicorn.run(
                app,
                host=APP_CONFIG.viralcutter_host,
                port=7860,
            )
