"""Unit tests for download_video cookie handling and YouTube bot-check detection."""
import os
import sys
import unittest
from unittest.mock import patch

# Add repository root and scripts directory to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

import download_video


class TestDownloadVideoCookieHandling(unittest.TestCase):
    """Tests for cookie-browser candidate selection and bot-check detection."""

    @patch.dict(os.environ, {}, clear=True)
    @patch('download_video.sys.platform', 'win32')
    def test_get_cookie_browser_candidates_windows_defaults(self):
        candidates = download_video._get_cookie_browser_candidates()
        self.assertIn('chrome', candidates)
        self.assertIn('edge', candidates)

    @patch.dict(os.environ, {'YT_DLP_COOKIES_BROWSER': 'firefox'}, clear=True)
    def test_get_cookie_browser_candidates_honors_env(self):
        candidates = download_video._get_cookie_browser_candidates()
        self.assertEqual(candidates[0], 'firefox')

    def test_is_bot_check_error_matches_youtube_message(self):
        error_message = (
            "ERROR: [youtube] OXzk5P16RxQ: Sign in to confirm you're not a bot. "
            "Use --cookies-from-browser or --cookies for the authentication."
        )
        self.assertTrue(download_video._is_bot_check_error(error_message))

    def test_dedupe_preserve_order_can_be_filtered_for_none(self):
        ordered = download_video._dedupe_preserve_order([None, 'chrome', 'chrome'])
        filtered = [browser for browser in ordered if browser is not None]
        self.assertEqual(filtered, ['chrome'])

    @patch.dict(os.environ, {'YT_DLP_COOKIES_FILE': '/tmp/cookies.txt'}, clear=True)
    @patch('download_video.os.path.exists', return_value=True)
    def test_get_cookie_file_from_env_returns_existing_file(self, _exists):
        cookie_file = download_video._get_cookie_file_from_env()
        expected = os.path.abspath(os.path.expanduser('/tmp/cookies.txt'))
        self.assertEqual(cookie_file, expected)

    @patch.dict(os.environ, {}, clear=True)
    @patch('download_video.sys.platform', 'linux')
    @patch('download_video.os.path.exists', return_value=False)
    def test_filter_cookie_browser_candidates_skips_missing_linux_profiles(
        self,
        _exists,
    ):
        candidates = ['chrome', 'firefox']
        filtered = download_video._filter_cookie_browser_candidates(candidates)
        self.assertEqual(filtered, [])


if __name__ == '__main__':
    unittest.main()
