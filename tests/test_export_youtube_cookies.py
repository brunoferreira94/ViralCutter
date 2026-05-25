"""Tests for automatic YouTube cookie export helper."""

import os
import sys
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

import export_youtube_cookies


class TestExportYoutubeCookies(unittest.TestCase):
    def test_build_export_command_includes_required_flags(self):
        cmd = export_youtube_cookies.build_export_command(
            browser='chrome',
            output_path='/tmp/cookies.txt',
            url='https://www.youtube.com/watch?v=abc123',
        )

        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1], '-m')
        self.assertEqual(cmd[2], 'yt_dlp')
        self.assertIn('--cookies-from-browser', cmd)
        self.assertIn('chrome', cmd)
        self.assertIn('--cookies', cmd)
        self.assertIn('/tmp/cookies.txt', cmd)

    def test_resolve_output_path_returns_absolute(self):
        path = export_youtube_cookies.resolve_output_path('cookies/youtube.txt')
        self.assertTrue(os.path.isabs(path))
        self.assertTrue(path.endswith(os.path.join('cookies', 'youtube.txt')))

    @patch('export_youtube_cookies.subprocess.run')
    def test_export_cookies_executes_subprocess(self, mock_run):
        mock_run.return_value.returncode = 0
        with TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'cookies.txt')
            with open(output_path, 'w', encoding='utf-8') as cookie_file:
                cookie_file.write('# Netscape HTTP Cookie File\n')
                cookie_file.write('.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tabc\n')

            exit_code = export_youtube_cookies.export_cookies(
                browser='firefox',
                output_path=output_path,
                url='https://www.youtube.com',
            )

        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once()

    @patch('export_youtube_cookies.subprocess.run')
    def test_export_cookies_accepts_existing_file_even_with_non_zero_return(
        self,
        mock_run,
    ):
        mock_run.return_value.returncode = 1

        with TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'cookies.txt')
            with open(output_path, 'w', encoding='utf-8') as cookie_file:
                cookie_file.write('# Netscape HTTP Cookie File\n')
                cookie_file.write('.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tabc\n')

            exit_code = export_youtube_cookies.export_cookies(
                browser='firefox',
                output_path=output_path,
                url='https://www.youtube.com',
            )

        self.assertEqual(exit_code, 0)

    def test_filter_cookie_file_keeps_only_relevant_domains(self):
        with TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'cookies.txt')
            with open(output_path, 'w', encoding='utf-8') as cookie_file:
                cookie_file.write('# Netscape HTTP Cookie File\n')
                cookie_file.write('.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tabc\n')
                cookie_file.write('.example.com\tTRUE\t/\tFALSE\t0\tID\t123\n')

            kept = export_youtube_cookies.filter_cookie_file(output_path)

            with open(output_path, 'r', encoding='utf-8') as cookie_file:
                content = cookie_file.read()

        self.assertEqual(kept, 1)
        self.assertIn('.youtube.com', content)
        self.assertNotIn('.example.com', content)

    def test_filter_cookie_file_removes_large_and_excluded_google_cookies(self):
        with TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'cookies.txt')
            with open(output_path, 'w', encoding='utf-8') as cookie_file:
                cookie_file.write('# Netscape HTTP Cookie File\n')
                cookie_file.write(
                    'accounts.google.com\tFALSE\t/\tTRUE\t0\t'
                    'ACCOUNT_CHOOSER\tverylongvalue\n'
                )
                cookie_file.write(
                    '.google.com\tTRUE\t/\tTRUE\t0\tSAPISID\t'
                    + ('x' * 700)
                    + '\n'
                )
                cookie_file.write('.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tabc\n')

            kept = export_youtube_cookies.filter_cookie_file(output_path)

            with open(output_path, 'r', encoding='utf-8') as cookie_file:
                content = cookie_file.read()

        self.assertEqual(kept, 1)
        self.assertIn('.youtube.com', content)
        self.assertNotIn('ACCOUNT_CHOOSER', content)
        self.assertNotIn('SAPISID', content)

    def test_filter_cookie_file_removes_non_allowlisted_cookie_names(self):
        with TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'cookies.txt')
            with open(output_path, 'w', encoding='utf-8') as cookie_file:
                cookie_file.write('# Netscape HTTP Cookie File\n')
                cookie_file.write('.youtube.com\tTRUE\t/\tFALSE\t0\tST-abc\tvalue\n')
                cookie_file.write('.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tabc\n')

            kept = export_youtube_cookies.filter_cookie_file(output_path)

            with open(output_path, 'r', encoding='utf-8') as cookie_file:
                content = cookie_file.read()

        self.assertEqual(kept, 1)
        self.assertIn('SID', content)
        self.assertNotIn('ST-abc', content)


if __name__ == '__main__':
    unittest.main()
