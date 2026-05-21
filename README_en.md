# ViralCutter

[![Discord](https://dcbadge.limes.pink/api/server/tAdPHFAbud)](https://discord.gg/tAdPHFAbud)<br>

**100% Free, Local, and Unlimited Open-Source Alternative to Opus Clip**  
Turn long YouTube videos into viral shorts optimized for TikTok, Instagram Reels, and YouTube Shorts – with state-of-the-art AI, dynamic captions, precise _face tracking_, and automatic translation. All running on your machine.

[![Stars](https://img.shields.io/github/stars/RafaelGodoyEbert/ViralCutter?style=social)](https://github.com/RafaelGodoyEbert/ViralCutter/stargazers)
[![Forks](https://img.shields.io/github/forks/RafaelGodoyEbert/ViralCutter?style=social)](https://github.com/RafaelGodoyEbert/ViralCutter/network/members)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1UZKzeqjIeEyvq9nPx7s_4mU6xlkZQn_R?usp=sharing)

[English](README_en.md) • [Português](README.md)

## Why is ViralCutter a "Game Changer"?

Forget expensive subscriptions and minute limits. ViralCutter offers unlimited power on your own hardware.

| Feature           | ViralCutter (Open-Source)                                    | Opus Clip / Klap / Munch (SaaS) |
| :---------------- | :----------------------------------------------------------- | :------------------------------ |
| **Price**         | **Free & Unlimited**                                         | $20–$100/mo + minute limits     |
| **Privacy**       | **100% Local** (Your data never leaves your PC)              | Upload to third-party cloud     |
| **AI & LLM**      | **Flexible**: Gemini (Free), GPT-4, **Local GGUF (Offline)** | Only what they offer            |
| **Face Tracking** | **Split Screen (2 faces)**, Active Speaker (Exp.), Auto      | Basic or extra cost             |
| **Translation**   | **Yes** (Translate captions to 10+ languages)                | Limited features                |
| **Editing**       | **Export XML to Premiere Pro** (Beta)                        | Limited web editor              |
| **Watermark**     | **ZERO**                                                     | Yes (on free plans)             |

**Professional results, total privacy, and zero cost.**

## Key Features 🚀

- 🤖 **AI Viral Cut**: Automatically identifies hooks and engaging moments using **Gemini**, **GPT-4**, or **Local LLMs (Llama 3, DeepSeek, etc)**.
- 🗣️ **Ultra-Precise Transcription**: Powered by **WhisperX** with GPU acceleration for perfect subtitles.
- 🎨 **Dynamic Captions**: "Hormozi" style with word-by-word highlights, vibrant colors, emojis, and full customization.
- 🎥 **Auto Camera Direction**:
  - **Auto-Crop 9:16**: Transforms horizontal to vertical while keeping the focus.
  - **Smart Split Screen**: Detects 2 people talking and automatically splits the screen.
  - **Active Speaker (Experimental)**: The camera cuts to whoever is speaking.
- 🌍 **Video Translation**: Automatically generate translated subtitles (e.g., English Video -> Portuguese Subtitles).
- 💾 **Quality & Control**: Choose resolution (up to 4K/Best), format output, and save processing configurations.
- ⚡ **Performance**: Transcription with "slicing" (process 1x, cut N times) and ultra-fast installation via `uv`.
- 🖥️ **Modern Interface**: Gradio WebUI, Dark Mode, Project Gallery, and integrated Subtitle Editor.

## Web Interface (Inspired by Opus Clip)

![WebUI Home](https://github.com/user-attachments/assets/ba147149-fc5f-48fc-a03c-fc86b5dc0568)
_Intuitive control panel with fine-tuning for AI and rendering._

![WebUi Library](https://github.com/user-attachments/assets/b0204e4b-0e5d-4ee4-b7b4-cac044b76c24)
_Library: OpusClip-style gallery and intuitive controls_

## Local Installation (Super Fast ⚡)

### Prerequisites (From Scratch Setup)

To run ViralCutter on a fresh computer, you need to install the following core tools:

1. **Visual Studio C++ Build Tools**
   Required to compile `insightface` and avoid "Cpp/Visual Studio" setup errors.
   - Download [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
   - Run the installer and check the **"Desktop development with C++"** box.
   - Ensure _Windows 10/11 SDK_ and _MSVC v143 - VS 2022 C++_ are checked on the right panel, then click install. Restart your PC if prompted.

2. **Python (3.10.x or 3.11.x recommended)**
   - Download from [python.org/downloads](https://www.python.org/downloads/).
   - ⚠️ **VERY IMPORTANT:** On the very first setup screen, mark the checkbox **"Add Python to PATH"** at the bottom before clicking install.

3. **FFmpeg** (Audio/Video Processing Engine)
   - The easiest way on Windows is to open your terminal (PowerShell) as Administrator and run:
     `winget install ffmpeg`
   - Restart the terminal and type `ffmpeg -version` to confirm it works.

4. **Video Card Drivers (NVIDIA)**
   - Keep your drivers updated (via GeForce Experience or the Nvidia website) to support CUDA 12.4+ acceleration.
   - **NVIDIA GPU** is highly recommended for speed and local AI operations.

---

### Step-by-Step Installation

1.  **Install Dependencies via Script**
    Open the ViralCutter folder and double-click **one of the installers** below:
    - `install_dependencies.bat`: **Standard** installation (Recommended). Faster and fail-proof. Uses cloud AIs like Gemini (Free) and GPT-4.
    - `install_dependencies_advanced_LocalLLM.bat`: **Advanced** installation. Dedicated for users who want to run full offline AIs on their hardware (Llama 3, etc). Requires a good GPU and _C++ Build Tools_.

    _(Both use the `uv` package manager to set everything up automatically)._

2.  **Configure AI (Optional)**
    - **Gemini (Recommended/Free)**: Add your key in `api_config.json`.
  - **GitHub Copilot (official SDK)**: Use OAuth App in WebUI (Start/Finish login) or provide a Copilot SDK-compatible token in `api_config.json`.
    - **Local (GGUF)**: Download your favorite `.gguf` models and place them in the `models/` folder. ViralCutter will detect them automatically.

3.  **Run**
    - Double-click `run_webui.bat` to open the interface in your browser.
    - Or use `python main_improved.py` for the CLI version.

## GitHub Copilot SDK in ViralCutter

The integration uses the official `github-copilot-sdk` client with a dedicated Python bridge.

### Quick setup

1. Set OAuth App environment variables (recommended for WebUI):
   - `COPILOT_OAUTH_CLIENT_ID`
   - `COPILOT_OAUTH_CLIENT_SECRET` (if required)
2. Open WebUI (`run_webui.bat` or `python webui/app.py`)
   - Select **GitHub Copilot** as AI backend
   - Click **Start Copilot OAuth Login** and authorize on GitHub
   - Click **Finish Copilot OAuth Login** to persist the token
3. Choose a model available in your Copilot SDK account (example: `gpt-4.1`).

Optional `api_config.json` block:

```json
"copilot": {
  "github_token": "gho_or_ghu_TOKEN_HERE",
  "model": "gpt-4.1",
  "chunk_size": 10000
}
```

CLI example:

```bash
python main_improved.py --ai-backend copilot --api-key gho_or_ghu_TOKEN_HERE --ai-model-name gpt-4.1
```

### Copilot troubleshooting

- **401 / invalid or expired token**:
  - Generate a new OAuth/fine-grained token compatible with Copilot SDK.
- **403 / insufficient permissions**:
  - Reissue token with proper Copilot access.
- **OAuth flow does not complete in WebUI**:
  - Validate `COPILOT_OAUTH_CLIENT_ID` and `COPILOT_OAUTH_CLIENT_SECRET`.
- **SDK bridge failure**:
  - Ensure dependencies are installed and `github-copilot-sdk` is available.

### Quick verification

```bash
python -c "import copilot; print('OK copilot-sdk')"
python -m py_compile scripts/copilot_sdk_bridge.py scripts/github_copilot_provider.py scripts/create_viral_segments.py
```

## Docker (Windows, macOS, and Linux)

If you prefer reproducible and OS-agnostic setup, use the official Docker artifacts:

- `Dockerfile` (CPU, default)
- `Dockerfile.gpu` (NVIDIA GPU, optional)
- `docker-compose.yml` (WebUI/CLI profiles)

### Prerequisites

- Docker Engine + Docker Compose Plugin (`docker compose`)
- For GPU mode: NVIDIA Driver + NVIDIA Container Toolkit installed on host

### 1) Run WebUI (CPU)

```bash
docker compose --profile webui up --build webui
```

Open: `http://localhost:7860`

### 2) Run CLI (CPU)

```bash
docker compose --profile cli run --rm cli --help
```

Example with URL:

```bash
docker compose --profile cli run --rm cli --url "https://www.youtube.com/watch?v=VIDEO_ID" --segments 3 --viral
```

### 3) Run WebUI (NVIDIA GPU)

```bash
docker compose --profile webui-gpu up --build webui-gpu
```

### 4) Run CLI (NVIDIA GPU)

```bash
docker compose --profile cli-gpu run --rm cli-gpu --help
```

### Persistent volumes

`docker-compose.yml` already mounts:

- `./VIRALS` -> `/app/VIRALS`
- `./models` -> `/app/models`
- `./api_config.json` -> `/app/api_config.json`
- `./prompt.txt` -> `/app/prompt.txt`

This keeps outputs, model assets, and runtime config between runs without rebuilding images.

### Migration from `.bat` scripts to Docker

- `run_webui.bat` -> `docker compose --profile webui up --build webui`
- `run.bat` (CLI) -> `docker compose --profile cli run --rm cli ...args...`

### Quick troubleshooting

- Port `7860` already in use:
  - Change mapping in `docker-compose.yml` (for example, `7861:7860`).
- Volume permission issues on Linux/macOS:
  - Adjust local folder permissions (`VIRALS`, `models`) for your Docker user.
- GPU not detected:
  - Validate `nvidia-smi` on host and NVIDIA Container Toolkit installation.
- Slow first build:
  - Initial build is heavy due to ML dependencies; later builds use Docker layer cache.

## Output Examples

**Viral Clip with Highlight Captions**  
<video src="https://github.com/user-attachments/assets/7a32edce-fa29-4693-985f-2b12313362f3" controls></video>

**Direct Comparison: Opus Clip vs ViralCutter** (same input video)  
<video src="https://github.com/user-attachments/assets/12916792-dc0e-4f63-a76b-5698946f50f4" controls></video>

**2-Face Split Screen Mode**  
<video src="https://github.com/user-attachments/assets/f5ce5168-04a2-4c9b-9408-949a5400d020" controls></video>

## Roadmap (TODO)

- [x] Release code
- [ ] Permanent Demo on Hugging Face Spaces
- [x] Two face in the cut (Split Screen)
- [x] Custom caption and burn
- [x] Make the code faster
- [x] 100% Local AI Models (Ollama/Llama/GGUF)
- [x] Automatic caption translation
- [x] The cut follows the face as it moves
- [x] XML Export to Premiere Pro (Beta)
- [ ] Automatic background music (Auto-Duck)
- [ ] Direct upload to TikTok/YouTube/Instagram
- [ ] More framing formats (beyond 9:16)
- [ ] Optional Watermark

---

## Contribute!

ViralCutter is community-maintained. Join us to democratize AI content creation!

- **Discord**: [AI Hub Brasil](https://discord.gg/aihubbrasil)
- **Github**: Give us a ⭐ star if this project helped you!

**Current Version**: 0.8v Alpha
_ViralCutter: Because viral clips shouldn't cost a fortune._ 🚀
