import unittest

from config import COPILOT_MODELS, DEFAULT_COPILOT_MODEL


class TestConfig(unittest.TestCase):
    def test_default_copilot_model_is_listed(self):
        self.assertIn(DEFAULT_COPILOT_MODEL, COPILOT_MODELS)

    def test_copilot_models_include_gpt_and_claude_families(self):
        self.assertIn("gpt-4.1", COPILOT_MODELS)
        self.assertIn("gpt-4o", COPILOT_MODELS)
        self.assertIn("claude-3-5-sonnet-20241022", COPILOT_MODELS)


if __name__ == "__main__":
    unittest.main()
