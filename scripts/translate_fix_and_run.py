import sys
import json
import asyncio
from pathlib import Path
import importlib.util

# Import translate_json by path so the script works even when 'scripts' is not a package
spec = importlib.util.spec_from_file_location("translate_json", str(Path(__file__).parent / "translate_json.py"))
translate_json = importlib.util.module_from_spec(spec)
spec.loader.exec_module(translate_json)

translate_json_file = translate_json.translate_json_file
adjust_segments = translate_json.adjust_segments
_normalize_target_lang = translate_json._normalize_target_lang

if len(sys.argv) < 3:
    print('Usage: translate_fix_and_run.py <project_folder> <target_lang>')
    sys.exit(1)

project_folder = Path(sys.argv[1])
subs_folder = project_folder / 'subs'
if not subs_folder.exists():
    print(f'Subtitle folder not found: {subs_folder}')
    sys.exit(0)

json_files = list(subs_folder.glob('*_processed.json'))
if not json_files:
    print('No subtitle files found to translate.')
    sys.exit(0)

normalized = _normalize_target_lang(sys.argv[2])
print(f'Found {len(json_files)} files. Translating to {sys.argv[2]} (normalized: {normalized})...')

async def do_file(json_file, target_lang):
    # Ensure words exist
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = data.get('segments', [])
    if segments and 'words' not in segments[0]:
        print(f'Adding words to {json_file.name} using safe generator')
        # Safe generation of words without relying on existing 'words' keys
        new_segments = []
        for idx, seg in enumerate(segments):
            text_words = seg.get('text', '').split() or ['']
            seg_duration = max(0.001, seg.get('end', seg.get('start', 0)) - seg.get('start', 0))
            words = []
            for wi, w in enumerate(text_words):
                start = seg.get('start', 0) + wi * (seg_duration / len(text_words))
                end = seg.get('start', 0) + (wi + 1) * (seg_duration / len(text_words))
                words.append({'word': w, 'start': start, 'end': end, 'score': 1.0})
            # extend last word to at most +2s or next segment start if available
            if idx + 1 < len(segments):
                next_start = segments[idx + 1].get('start', seg.get('end', seg.get('start', 0)))
                words[-1]['end'] = min(next_start, words[-1]['start'] + 2)
                seg['end'] = words[-1]['end']
            else:
                words[-1]['end'] = min(seg.get('end', seg.get('start', 0)) + 2, words[-1]['start'] + 2)
                seg['end'] = words[-1]['end']
            seg['words'] = words
            new_segments.append(seg)
        data['segments'] = new_segments
        # backup
        backup = json_file.with_name(json_file.stem + '_original' + json_file.suffix)
        if not backup.exists():
            json_file.rename(backup)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            # overwrite original with new segments
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # After ensuring 'words' exist, call translator using the current file as source
    await translate_json_file(json_file, json_file, target_lang)

async def main():
    for jf in json_files:
        try:
            await do_file(jf, normalized)
        except Exception as e:
            print(f'Failed translating {jf.name}: {e}')

asyncio.run(main())
