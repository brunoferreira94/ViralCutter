import os
import copy
import re
import json
import yt_dlp
import sys
from i18n.i18n import I18nAuto
i18n = I18nAuto()


def _dedupe_preserve_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _get_cookie_browser_candidates():
    env_browser = os.getenv("YT_DLP_COOKIES_BROWSER", "").strip().lower()
    if env_browser:
        return [env_browser]

    if sys.platform.startswith("win"):
        return ["chrome", "edge", "brave", "firefox", "chromium", "opera"]
    if sys.platform == "darwin":
        return ["chrome", "safari", "brave", "firefox", "chromium", "opera"]
    return ["chrome", "chromium", "brave", "firefox", "edge", "opera"]


def _get_cookie_file_from_env():
    cookie_file = os.getenv("YT_DLP_COOKIES_FILE", "").strip()
    if not cookie_file:
        return None

    resolved = os.path.abspath(os.path.expanduser(cookie_file))
    if not os.path.exists(resolved):
        print(i18n("Warning: YT_DLP_COOKIES_FILE not found: {}").format(resolved))
        return None
    return resolved


def _filter_cookie_browser_candidates(candidates):
    forced_browser = os.getenv("YT_DLP_COOKIES_BROWSER", "").strip()
    if forced_browser:
        return candidates

    if sys.platform.startswith("win") or sys.platform == "darwin":
        return candidates

    linux_paths = {
        "chrome": [
            "~/.config/google-chrome",
            "~/.var/app/com.google.Chrome",
        ],
        "chromium": [
            "~/.config/chromium",
        ],
        "brave": [
            "~/.config/BraveSoftware/Brave-Browser",
        ],
        "firefox": [
            "~/.config/mozilla/firefox",
            "~/.mozilla/firefox",
        ],
        "edge": [
            "~/.config/microsoft-edge",
        ],
        "opera": [
            "~/.config/opera",
        ],
    }

    available = []
    for browser in candidates:
        known_paths = linux_paths.get(browser, [])
        if any(os.path.exists(os.path.expanduser(path)) for path in known_paths):
            available.append(browser)

    return available


def _is_bot_check_error(error_message):
    msg = (error_message or "").lower()
    return (
        "sign in to confirm you're not a bot" in msg
        or "use --cookies-from-browser" in msg
        or "use --cookies" in msg
    )


def _download_with_current_opts(url, ydl_opts, download_subs):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        if "No address associated with hostname" in error_str or "Failed to resolve" in error_str:
            print(i18n("\n[CRITICAL ERROR] Connection Failure: Could not access YouTube."))
            print(i18n("Check your internet connection or if there is any DNS block."))
            print(i18n("Details: {}").format(e))
            sys.exit(1)

        if download_subs and ("Unable to download video subtitles" in error_str or "429" in error_str):
            print(i18n("\nWarning: Error downloading subtitles ({}).").format(e))
            print(i18n("Retrying ONLY the video (without subtitles)..."))

            ydl_opts['writesubtitles'] = False
            ydl_opts['writeautomaticsub'] = False
            ydl_opts['postprocessors'] = [p for p in ydl_opts.get('postprocessors', []) if 'Subtitle' not in p.get('key', '')]

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return
            except Exception as e2:
                print(i18n("Fatal error on second attempt: {}").format(e2))
                raise

        if "is not a valid URL" in error_str:
            print(i18n("Error: the entered link is not valid."))
            raise

        print(i18n("Download error: {}").format(e))
        raise
    except Exception as e:
        print(i18n("Unexpected error: {}").format(e))
        raise

def sanitize_filename(name):
    """Remove caracteres inválidos e emojis para evitar erro de encoding no Windows."""
    # Remove caracteres reservados do sistema de arquivos
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    
    # Remove emojis e caracteres não suportados pelo console Windows (CP1252)
    # Isso mantém acentos (á, ç, é) mas remove 😱, etc.
    try:
        cleaned = cleaned.encode('cp1252', 'ignore').decode('cp1252')
    except:
        # Fallback se não tiver CP1252: remove tudo não-ascii (remove acentos)
        cleaned = cleaned.encode('ascii', 'ignore').decode('ascii')
        
    cleaned = cleaned.strip()
    return cleaned

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '').replace('%','')
            print(f"[download] {p}% - {d.get('_eta_str', 'N/A')} remaining", flush=True)
        except:
            pass
    elif d['status'] == 'finished':
        print(f"[download] Download concluído: {d['filename']}", flush=True)

def download(url, base_root="VIRALS", download_subs=True, quality="best"):
    # 1. Extrair informações do vídeo para pegar o título
    print(i18n("Extracting video information..."))
    title = None
    cookie_file = _get_cookie_file_from_env()
    selected_cookie_browser = None
    cookie_browser_candidates = _filter_cookie_browser_candidates(
        _get_cookie_browser_candidates()
    )

    if cookie_file:
        try:
            with yt_dlp.YoutubeDL(
                {
                    'quiet': True,
                    'no_warnings': True,
                    'cookiefile': cookie_file,
                }
            ) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title')
        except Exception as e:
            print(i18n("Warning: Failed to extract info with cookie file: {}").format(e))

    if not cookie_browser_candidates and not cookie_file:
        print(
            i18n(
                "No browser cookies found in this environment. "
                "Set YT_DLP_COOKIES_FILE with a Netscape cookies.txt file."
            )
        )

    # Tentativas com cookies de navegador para reduzir bloqueio anti-bot.
    for browser in cookie_browser_candidates if not title else []:
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'cookiesfrombrowser': (browser,)}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title')
                if title:
                    selected_cookie_browser = browser
                    break
        except Exception as e:
            try:
                print(i18n("Warning: Failed to extract info with cookies: {}").format(e))
            except UnicodeEncodeError:
                print(i18n("Warning: Failed to extract info with cookies: [Encoding Error in Message]"))

    # Tentativa sem cookies
    if not title:
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title')
        except Exception as e:
            try:
                print(i18n("Error getting video info (without cookies): {}").format(e))
            except UnicodeEncodeError:
                print(i18n("Error getting video info (without cookies): [Encoding Error in Message]"))

    # Fallback final
    if title:
        safe_title = sanitize_filename(title)
        try:
            print(i18n("Detected title: {}").format(title))
        except UnicodeEncodeError:
            # Fallback for Windows consoles that choke on Emojis
            clean_title = title.encode('ascii', 'replace').decode('ascii')
            print(i18n("Detected title: {}").format(clean_title))
    else:
        print(i18n("WARNING: Title could not be obtained. Using 'Unknown_Video'."))
        safe_title = i18n("Unknown_Video")

    # 2. Criar estrutura de pastas
    project_folder = os.path.join(base_root, safe_title)
    os.makedirs(project_folder, exist_ok=True)
    
    # Caminho final do vídeo
    output_filename = 'input' 
    output_path_base = os.path.join(project_folder, output_filename)
    final_video_path = f"{output_path_base}.mp4"

    # Verificação inteligente
    if os.path.exists(final_video_path):
        if os.path.getsize(final_video_path) > 1024: 
            try:
                print(i18n("Video already exists at: {}").format(final_video_path))
            except UnicodeEncodeError:
                print(i18n("Video already exists at: {}").format(final_video_path.encode('ascii', 'replace').decode('ascii')))
            print(i18n("Skipping download and reusing local file."))
            return final_video_path, project_folder
        else:
            print(i18n("Existing file found but seems corrupted/empty. Downloading again..."))
            try:
                os.remove(final_video_path)
            except:
                pass

    # Limpeza de temp
    temp_path = f"{output_path_base}.temp.mp4"
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass

    # Mapeamento de Qualidade
    quality_map = {
        "best": 'bestvideo+bestaudio/best',
        "1080p": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        "720p": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        "480p": 'bestvideo[height<=480]+bestaudio/best[height<=480]'
    }
    selected_format = quality_map.get(quality, 'bestvideo+bestaudio/best')
    print(i18n("Configuring download quality: {} -> {}").format(quality, selected_format))

    ydl_opts = {
        'format': selected_format,
        'overwrites': True,
        'outtmpl': output_path_base, 
        'postprocessor_args': [
            '-movflags', 'faststart'
        ],
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        # Opções de Legenda
        'writesubtitles': download_subs,
        'writeautomaticsub': download_subs,
        'subtitleslangs': ['pt-BR', 'pt', 'pt.*', 'pt-BR.*', 'en.*', 'sp.*'], # Prioritize pt-BR, then PT generic, then EN/SP
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'skip_download': False,
        'quiet': False,
        'no_warnings': False,
        'force_ipv4': True,
    }
    

    
    if download_subs:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }]

    try:
        print(i18n("Downloading video to: {}...").format(project_folder))
    except UnicodeEncodeError:
        print(i18n("Downloading video to: {}...").format(project_folder.encode('ascii', 'replace').decode('ascii')))

    # Prioriza o browser que funcionou na extração do título.
    cookie_attempts = []
    if cookie_file:
        cookie_attempts.append(("cookiefile", cookie_file))
    ordered_browsers = _dedupe_preserve_order([
        selected_cookie_browser,
        *cookie_browser_candidates,
    ])
    cookie_attempts.extend(
        ("browser", browser)
        for browser in ordered_browsers
        if browser is not None
    )
    cookie_attempts.append(("none", None))

    last_download_error = None
    for attempt_type, value in cookie_attempts:
        attempt_opts = copy.deepcopy(ydl_opts)
        if attempt_type == "cookiefile":
            attempt_opts['cookiefile'] = value
        elif attempt_type == "browser":
            attempt_opts['cookiesfrombrowser'] = (value,)

        try:
            _download_with_current_opts(url, attempt_opts, download_subs)
            last_download_error = None
            break
        except yt_dlp.utils.DownloadError as e:
            last_download_error = e
            if _is_bot_check_error(str(e)) and attempt_type == "browser":
                print(i18n("Warning: Cookie attempt with browser '{}' failed. Trying next browser...").format(value))
                continue
            if _is_bot_check_error(str(e)) and attempt_type == "cookiefile":
                print(i18n("Warning: Cookie file authentication failed. Trying browser cookies..."))
                continue
            if _is_bot_check_error(str(e)) and attempt_type == "none":
                print(i18n("Authentication required by YouTube. Set YT_DLP_COOKIES_FILE to a valid cookies.txt file or define YT_DLP_COOKIES_BROWSER."))
            raise

    if last_download_error is not None:
        raise last_download_error

    # RENOMEAR LEGENDA PARA PADRÃO (input.vtt ou input.srt)
    # Se for VTT, converte para SRT para garantir compatibilidade.
    try:
        import glob
        # Pega a primeira que encontrar
        potential_subs = glob.glob(os.path.join(project_folder, "input.*.vtt")) + glob.glob(os.path.join(project_folder, "input.*.srt"))
        
        if potential_subs:
            best_sub = potential_subs[0]
            ext = os.path.splitext(best_sub)[1]
            new_name = os.path.join(project_folder, "input.srt") # Vamos padronizar tudo para .srt
            subtitle_source_match = re.search(r"input(?:\.([^.]+))?\.(?:vtt|srt)$", os.path.basename(best_sub), re.IGNORECASE)
            subtitle_source_lang = subtitle_source_match.group(1) if subtitle_source_match and subtitle_source_match.group(1) else "unknown"
            subtitle_source_info = {
                "source_file": os.path.basename(best_sub),
                "source_language": subtitle_source_lang,
                "normalized_target": "input.srt"
            }
            subtitle_source_path = os.path.join(project_folder, "input.subtitle_source.json")
            try:
                with open(subtitle_source_path, "w", encoding="utf-8") as meta_file:
                    json.dump(subtitle_source_info, meta_file, ensure_ascii=False, indent=2)
                print(i18n("Subtitle source detected: {} (lang: {})").format(subtitle_source_info["source_file"], subtitle_source_info["source_language"]))
            except Exception as e_meta:
                print(i18n("Warning: Could not write subtitle source metadata: {}").format(e_meta))
            
            if ext.lower() == '.vtt':
                try:
                    print(i18n("Formatting complex VTT subtitle ({}) to clean SRT...").format(os.path.basename(best_sub)))
                except UnicodeEncodeError:
                    print(i18n("Formatting complex VTT subtitle ({}) to clean SRT...").format(os.path.basename(best_sub).encode('ascii', 'replace').decode('ascii')))
                try:
                    with open(best_sub, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    srt_content = []
                    counter = 1
                    
                    seen_texts = set()
                    last_text = ""
                    
                    for line in lines:
                        clean_line = line.strip()
                        # Ignora Headers e Metadados do VTT/Youtube
                        if clean_line.startswith("WEBVTT") or \
                           clean_line.startswith("X-TIMESTAMP") or \
                           clean_line.startswith("NOTE") or \
                           clean_line.startswith("Kind:") or \
                           clean_line.startswith("Language:"):
                            continue
                        
                        if "-->" in clean_line:
                            # Parse Timestamp
                            parts = clean_line.split("-->")
                            start = parts[0].strip()
                            # Remove tags de posicionamento "align:start position:0%"
                            end = parts[1].strip().split(' ')[0] 
                            
                            def fix_time(t):
                                t = t.replace('.', ',')
                                if t.count(':') == 1: 
                                    t = "00:" + t
                                return t
                            
                            current_start = fix_time(start)
                            current_end = fix_time(end)
                            
                        elif clean_line:
                             # Texto: remover tags complexas <00:00:00.560><c> etc
                             # O YouTube usa formato karaoke. Ex: "Quanto<...> custa<...>"
                             # Precisamos do texto limpo.
                             text = re.sub(r'<[^>]+>', '', clean_line).strip()
                             
                             if not text: continue
                             
                             # Lógica para remover duplicatas do estilo "Roll-up" ou "Karaoke"
                             # O YouTube repete a linha anterior às vezes.
                             # Ex:
                             # 1: "Quanto custa"
                             # 2: "Quanto custa\nQuantos quilos"
                             
                             # Vamos pegar apenas a ULTIMA linha se tiver quebras
                             lines_in_text = text.split('\n')
                             final_line = lines_in_text[-1].strip()
                             
                             if not final_line: continue

                             # Filtro de duplicidade consecutivo
                             if final_line == last_text:
                                 continue
                             
                             # Evita blocos ultra curtos (glitch de 10ms) que repetem texto
                             # Mas aqui estamos processando texto.
                             
                             srt_content.append(f"{counter}\n")
                             srt_content.append(f"{current_start} --> {current_end}\n")
                             srt_content.append(f"{final_line}\n\n")
                             
                             last_text = final_line
                             counter += 1
                    
                    with open(new_name, 'w', encoding='utf-8') as f_out:
                        f_out.writelines(srt_content)
                    
                    try:
                        print(i18n("Subtitle converted and cleaned: {}").format(new_name))
                    except UnicodeEncodeError:
                        print(i18n("Subtitle converted and cleaned: {}").format(new_name.encode('ascii', 'replace').decode('ascii')))
                    try: os.remove(best_sub) 
                    except: pass
                    
                except Exception as e_conv:
                    print(i18n("Failed to convert VTT: {}. Keeping original.").format(e_conv))
                    # Fallback: rename apenas
                    new_name_fallback = os.path.join(project_folder, "input.vtt")
                    if os.path.exists(new_name_fallback) and new_name_fallback != best_sub:
                        try: os.remove(new_name_fallback)
                        except: pass
                    os.rename(best_sub, new_name_fallback)

            else:
                # Já é SRT, só renomeia
                if os.path.exists(new_name) and new_name != best_sub:
                    try: os.remove(new_name)
                    except: pass
                os.rename(best_sub, new_name)
                try:
                    print(i18n("SRT subtitle renamed to: {}").format(new_name))
                except UnicodeEncodeError:
                    print(i18n("SRT subtitle renamed to: {}").format(new_name.encode('ascii', 'replace').decode('ascii')))
            
            # Limpa sobras
            for extra in potential_subs[1:]:
                try: os.remove(extra)
                except: pass

    except Exception as e_ren:
        print(i18n("Error processing subtitles: {}").format(e_ren))

    return final_video_path, project_folder