import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')

sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

import create_viral_segments as cvs


class TestCreateViralSegmentsCopilotMode(unittest.TestCase):
    def test_copilot_mode_does_not_require_anthropic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # transcript minimal para gerar ao menos 1 chunk
            with patch.object(cvs, 'load_transcript', return_value=[
                {'start': 0.0, 'end': 8.0, 'text': 'Trecho de teste para viral.'}
            ]), patch.object(cvs, 'HAS_COPILOT', True), patch.object(
                cvs,
                'call_copilot',
                return_value='{"segments":[{"start_time":1,"end_time":12,"title":"Hook","score":99}]}'
            ) as mocked_call:
                result = cvs.create(
                    num_segments=1,
                    viral_mode=True,
                    themes='',
                    tempo_minimo=5,
                    tempo_maximo=60,
                    ai_mode='copilot',
                    api_key='ghp_test_token',
                    project_folder=tmpdir,
                    chunk_size_arg=1000,
                    model_name_arg='gpt-4.1'
                )

            self.assertIn('segments', result)
            self.assertGreaterEqual(len(result['segments']), 1)
            mocked_call.assert_called()


if __name__ == '__main__':
    unittest.main()
