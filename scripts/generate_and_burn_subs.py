import os
import sys
import json
from scripts import transcribe_video, adjust_subtitles, burn_subtitles


def find_input_file(project_folder):
    candidates = ["input.mp4", "input_video.mp4"]
    for c in candidates:
        p = os.path.join(project_folder, c)
        if os.path.exists(p):
            return p
    return None


def main(project_folder="tmp", model_name="large-v3"):
    project_folder = os.path.abspath(project_folder)
    if not os.path.exists(project_folder):
        print(f"Project folder not found: {project_folder}")
        return 1

    input_file = find_input_file(project_folder)
    if not input_file:
        print("No input video found. Ensure input.mp4 or input_video.mp4 exists in the project folder.")
        return 2

    print(f"Transcribing/alinhando usando: {input_file}")
    try:
        srt, tsv = transcribe_video.transcribe(input_file, model_name, project_folder=project_folder)
    except Exception as e:
        print(f"Transcription/alignment failed: {e}")
        return 3

    # Expecting input.json to be created by transcribe_video (base name 'input')
    input_json_path = os.path.join(project_folder, "input.json")
    if not os.path.exists(input_json_path):
        # try to find any *.json in project_folder
        found = [f for f in os.listdir(project_folder) if f.endswith('.json')]
        if not found:
            print(f"No JSON transcript produced in {project_folder}")
            return 4
        input_json_path = os.path.join(project_folder, found[0])

    # Load input json and create subs/000_auto_processed.json
    subs_dir = os.path.join(project_folder, "subs")
    os.makedirs(subs_dir, exist_ok=True)

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed reading {input_json_path}: {e}")
        return 5

    processed = {"segments": data.get('segments', [])}
    out_name = os.path.join(subs_dir, "000_auto_processed.json")
    try:
        with open(out_name, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        print(f"Wrote processed subtitles: {out_name}")
    except Exception as e:
        print(f"Failed writing processed json: {e}")
        return 6

    # Subtitle config defaults (kept in sync with main_improved.get_subtitle_config)
    sub_config = {
        "font": "Montserrat-Regular",
        "base_size": 30,
        "base_color": "&H00FFFFFF&",
        "highlight_size": 35,
        "words_per_block": 3,
        "gap_limit": 0.5,
        "mode": 'highlight',
        "highlight_color": "&H00FF00&",
        "vertical_position": 210,
        "alignment": 2,
        "bold": 0,
        "italic": 0,
        "underline": 0,
        "strikeout": 0,
        "border_style": 2,
        "outline_thickness": 1.5,
        "outline_color": "&HFF808080&",
        "shadow_size": 2,
        "shadow_color": "&H000000&",
        "remove_punctuation": True,
    }

    try:
        print("Generating ASS files...")
        adjust_subtitles.adjust(project_folder=project_folder, **sub_config)
    except Exception as e:
        print(f"adjust_subtitles failed: {e}")
        return 7

    try:
        print("Burning subtitles into video(s)...")
        burn_subtitles.burn(project_folder=project_folder)
    except Exception as e:
        print(f"burn_subtitles failed: {e}")
        return 8

    print("Done.")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_and_burn_subs.py <project_folder> [model_name]")
        sys.exit(1)
    pf = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "large-v3"
    sys.exit(main(pf, model))
