"""Exporta cookies do navegador para um arquivo Netscape usando yt-dlp."""

import argparse
import os
import subprocess
import sys


MAX_COOKIE_VALUE_LENGTH = 512
EXCLUDED_COOKIE_NAMES = {
    "ACCOUNT_CHOOSER",
    "LSOLH",
}
ALLOWED_COOKIE_NAMES = {
    "CONSENT",
    "SOCS",
    "PREF",
    "YSC",
    "VISITOR_INFO1_LIVE",
    "VISITOR_PRIVACY_METADATA",
    "LOGIN_INFO",
    "SID",
    "HSID",
    "SSID",
    "APISID",
    "SAPISID",
    "SIDCC",
    "__Secure-1PSID",
    "__Secure-3PSID",
    "__Secure-1PAPISID",
    "__Secure-3PAPISID",
    "__Secure-1PSIDCC",
    "__Secure-3PSIDCC",
}


def resolve_output_path(output_path):
    """Resolve caminho de saida para absoluto."""
    expanded = os.path.expanduser(output_path)
    return os.path.abspath(expanded)


def build_export_command(browser, output_path, url):
    """Monta comando padrao de exportacao com yt-dlp."""
    return [
        sys.executable,
        "-m",
        "yt_dlp",
        "--cookies-from-browser",
        browser,
        "--cookies",
        output_path,
        "--skip-download",
        url,
    ]


def _is_cookie_header_line(line):
    normalized = line.strip()
    return normalized in (
        "# HTTP Cookie File",
        "# Netscape HTTP Cookie File",
    )


def is_relevant_cookie_domain(domain):
    normalized = domain.strip().lower()
    if normalized == "accounts.google.com":
        return False

    return normalized.endswith((
        "youtube.com",
        "google.com",
        "googlevideo.com",
        "ytimg.com",
    ))


def filter_cookie_file(cookie_file_path):
    with open(cookie_file_path, 'r', encoding='utf-8', errors='ignore') as handle:
        lines = handle.readlines()

    kept = []
    kept_count = 0

    for line in lines:
        if line.startswith('#') or not line.strip():
            kept.append(line)
            continue

        fields = line.split('\t')
        if len(fields) < 7:
            continue

        domain = fields[0]
        cookie_name = fields[5].strip()
        cookie_value = fields[6].strip()

        if cookie_name in EXCLUDED_COOKIE_NAMES:
            continue
        if cookie_name not in ALLOWED_COOKIE_NAMES:
            continue
        if len(cookie_value) > MAX_COOKIE_VALUE_LENGTH:
            continue

        if is_relevant_cookie_domain(domain):
            kept.append(line)
            kept_count += 1

    with open(cookie_file_path, 'w', encoding='utf-8') as handle:
        handle.writelines(kept)

    return kept_count


def is_valid_cookie_file(cookie_file_path):
    if not os.path.exists(cookie_file_path):
        return False

    with open(cookie_file_path, 'r', encoding='utf-8', errors='ignore') as handle:
        first_line = handle.readline()

    return _is_cookie_header_line(first_line)


def export_cookies(browser, output_path, url):
    """Executa exportacao e retorna o exit code."""
    output_abs = resolve_output_path(output_path)
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)

    cmd = build_export_command(browser=browser, output_path=output_abs, url=url)

    print("Exportando cookies com yt-dlp...")
    print(f"Browser: {browser}")
    print(f"Arquivo de saida: {output_abs}")

    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        if is_valid_cookie_file(output_abs):
            print(
                "Exportacao retornou erro de rede, mas o arquivo de cookies foi "
                "gerado. Continuando..."
            )
        else:
            print("Falha ao exportar cookies.")
            return result.returncode

    kept_count = filter_cookie_file(output_abs)
    print(f"Cookies relevantes mantidos: {kept_count}")

    if os.name != "nt":
        # Minimiza exposicao do arquivo de sessao em Unix.
        os.chmod(output_abs, 0o600)

    print("Cookies exportados com sucesso.")
    print("Use no container:")
    print(f"YT_DLP_COOKIES_FILE={output_abs}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Exporta cookies do YouTube para uso com yt-dlp em Docker/CLI."
    )
    parser.add_argument(
        "--browser",
        default=os.getenv("YT_DLP_COOKIES_BROWSER", "chrome"),
        help="Navegador para ler cookies (ex: chrome, edge, firefox).",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("YT_DLP_COOKIES_EXPORT_PATH", "cookies/youtube_cookies.txt"),
        help="Arquivo de saida (formato Netscape).",
    )
    parser.add_argument(
        "--url",
        default="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        help="URL usada para acionar exportacao dos cookies.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    return export_cookies(browser=args.browser, output_path=args.output, url=args.url)


if __name__ == "__main__":
    raise SystemExit(main())
