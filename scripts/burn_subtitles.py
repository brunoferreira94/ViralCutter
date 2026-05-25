import os
import subprocess
import sys
import json

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def burn_video_file(video_path, subtitle_path, output_path):
    """
    Burns subtitles into a single video file.
    """
    # Ajuste no caminho da legenda para FFmpeg (Forward Slash e escape de :)
    # No Windows, "C:/foo" funciona se estiver entre aspas simples dentro do filtro.
    # Para garantir, usamos replace e forward slashes.
    subtitle_file_ffmpeg = subtitle_path.replace('\\', '/').replace(':', '\\:')

    def run_ffmpeg(encoder, preset, additional_args=[]):
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error", "-hide_banner",
            '-i', video_path,
            '-vf', f"subtitles='{subtitle_file_ffmpeg}'",
            '-c:v', encoder,
            '-preset', preset,
            '-b:v', '5M',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            output_path
        ] + additional_args
        subprocess.run(cmd, check=True, capture_output=True)

    # Tentar NVENC primeiro
    try:
        # print(f"Processando vídeo (NVENC): {os.path.basename(video_path)}")
        run_ffmpeg("h264_nvenc", "p1")
        # print(f"Processado: {output_path}")
        return True, "NVENC Success"
    except subprocess.CalledProcessError as e:
        print(f"Erro com NVENC ({str(e)}). Tentando CPU (libx264)...")
        try:
            # Fallback CPU
            run_ffmpeg("libx264", "ultrafast")
            # print(f"Processado (CPU): {output_path}")
            return True, "CPU Success"
        except subprocess.CalledProcessError as e2:
            err_msg = f"ERRO FATAL ao queimar legendas em {os.path.basename(video_path)}: {e2}"
            if e2.stderr:
                 err_msg += f" | FFmpeg Log: {e2.stderr.decode('utf-8')}"
            print(err_msg)
            return False, err_msg
    except Exception as e:
        return False, str(e)

def burn(project_folder="tmp"):
    # Converter para absoluto para não ter erro no filtro do ffmpeg
    if project_folder and not os.path.isabs(project_folder):
        project_folder_abs = os.path.abspath(project_folder)
    else:
        project_folder_abs = project_folder

    # Caminhos das pastas
    subs_folder = os.path.join(project_folder_abs, 'subs_ass')
    videos_folder = os.path.join(project_folder_abs, 'final')
    output_folder = os.path.join(project_folder_abs, 'burned_sub')  # Pasta para salvar os vídeos com legendas

    # Cria a pasta de saída se não existir
    os.makedirs(output_folder, exist_ok=True)
    
    if not os.path.exists(videos_folder):
        print(f"Pasta de vídeos finais não encontrada: {videos_folder}")
        return

    expected_video_basenames = None
    viral_segments_path = os.path.join(project_folder_abs, "viral_segments.txt")
    if os.path.exists(viral_segments_path):
        try:
            with open(viral_segments_path, "r", encoding="utf-8") as vf:
                viral_data = json.load(vf)
            segments = viral_data.get("segments", [])
            if segments:
                expected_video_basenames = set()
                for idx, segment in enumerate(segments):
                    title = segment.get("title", f"Segment_{idx}")
                    safe_title = "".join([c for c in title if c.isalnum() or c in " _-"]).strip()
                    safe_title = safe_title.replace(" ", "_")[:60]
                    expected_video_basenames.add(f"{idx:03d}_{safe_title}")
                    expected_video_basenames.add(f"final-output{idx:03d}_processed")
        except Exception as e:
            print(f"Aviso: falha ao ler viral_segments.txt para filtrar burn: {e}")

    # Itera sobre os arquivos de vídeo na pasta final
    files = sorted(os.listdir(videos_folder))
    if not files:
        print("Nenhum arquivo encontrado em 'final' para queimar legendas.")
        return

    for video_file in files:
        if video_file.endswith(('.mp4', '.mkv', '.avi')):  # Formatos suportados
            # Se for temp file (ex: temp_video_no_audio), ignora se existir a versão final
            if "temp_video_no_audio" in video_file:
                continue

            # Extrai o nome base do vídeo (sem extensão)
            video_name = os.path.splitext(video_file)[0]

            if expected_video_basenames is not None and video_name not in expected_video_basenames:
                print(f"Ignorando arquivo extra em final: {video_file}")
                continue
            
            # Define o caminho para a legenda correspondente
            subtitle_file = os.path.join(subs_folder, f"{video_name}.ass")
            
            # Tentar também com sufixo _processed caso a convenção seja diferente
            if not os.path.exists(subtitle_file):
                subtitle_file_processed = os.path.join(subs_folder, f"{video_name}_processed.ass")
                if os.path.exists(subtitle_file_processed):
                    subtitle_file = subtitle_file_processed
            
            # Verifica se a legenda existe
            if os.path.exists(subtitle_file):
                # Define o caminho de saída para o vídeo com legendas
                output_file = os.path.join(output_folder, f"{video_name}_subtitled.mp4")

                print(f"Burning: {video_name}...")
                success, msg = burn_video_file(os.path.join(videos_folder, video_file), subtitle_file, output_file)
                if success:
                    print(f"Done: {output_file}")
                else:
                    print(f"Fail: {msg}")
            else:
                print(f"Legenda não encontrada para: {video_name} em {subtitle_file}")
