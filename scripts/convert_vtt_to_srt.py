import sys
import os
import re
import json


def fix_time(t):
    t = t.replace('.', ',')
    if t.count(':') == 1:
        t = '00:' + t
    return t


def convert(project_folder, lang='pt'):
    in_path = os.path.join(project_folder, f'input.{lang}.vtt')
    out_path = os.path.join(project_folder, 'input.srt')

    if not os.path.exists(in_path):
        print(f'No input.{lang}.vtt found at {in_path}')
        return 1

    with open(in_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    srt = []
    counter = 1
    last_text = ''
    current_start = None
    current_end = None

    for line in lines:
        clean = line.strip()
        if clean.startswith('WEBVTT') or clean.startswith('NOTE') or clean.startswith('Kind:') or clean.startswith('Language:') or clean.startswith('X-TIMESTAMP'):
            continue
        if '-->' in clean:
            parts = clean.split('-->')
            start = parts[0].strip()
            end = parts[1].strip().split()[0]
            current_start = fix_time(start)
            current_end = fix_time(end)
        elif clean:
            text = re.sub(r'<[^>]+>', '', clean).strip()
            if not text:
                continue
            final_line = text.split('\n')[-1].strip()
            if final_line == last_text:
                continue
            if current_start is None or current_end is None:
                continue
            srt.append(f"{counter}\n{current_start} --> {current_end}\n{final_line}\n\n")
            counter += 1
            last_text = final_line

    with open(out_path, 'w', encoding='utf-8') as o:
        o.writelines(srt)

    meta = {'source_file': os.path.basename(in_path), 'source_language': lang, 'normalized_target': 'input.srt'}
    with open(os.path.join(project_folder, 'input.subtitle_source.json'), 'w', encoding='utf-8') as m:
        json.dump(meta, m, ensure_ascii=False, indent=2)

    try:
        os.remove(in_path)
    except Exception as e:
        print('Warning: could not remove original vtt:', e)

    print('Converted to SRT and wrote input.subtitle_source.json')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: convert_vtt_to_srt.py <project_folder> [lang]')
        raise SystemExit(2)
    proj = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else 'pt'
    raise SystemExit(convert(proj, lang))
