"""
Unit tests for GitHub Copilot Provider integration.
"""
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import json

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from github_copilot_provider import GitHubCopilotProvider, create_copilot_provider


class TestGitHubCopilotProvider(unittest.TestCase):
    """Tests for GitHubCopilotProvider class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_token = "ghp_testtoken123456789"
        self.test_config = {
            "github_token": self.valid_token,
            "model": "claude-3-5-sonnet-20241022",
            "chunk_size": 10000
        }
    
    @patch('github_copilot_provider.Anthropic')
    def test_provider_initialization(self, mock_anthropic):
        """Test that provider initializes correctly."""
        provider = GitHubCopilotProvider(github_token=self.valid_token)
        
        # Verify Anthropic was initialized with correct token
        mock_anthropic.assert_called_once()
        self.assertIsNotNone(provider.client)
        self.assertEqual(provider.model, "claude-3-5-sonnet-20241022")
    
    @patch('github_copilot_provider.Anthropic')
    def test_provider_with_custom_model(self, mock_anthropic):
        """Test provider initialization with custom model."""
        custom_model = "claude-3-opus-20240229"
        provider = GitHubCopilotProvider(
            github_token=self.valid_token,
            model=custom_model
        )
        
        self.assertEqual(provider.model, custom_model)
    
    @patch('github_copilot_provider.Anthropic')
    def test_chunking_at_sentence_boundaries(self, mock_anthropic):
        """Test that transcript chunking respects sentence boundaries."""
        provider = GitHubCopilotProvider(github_token=self.valid_token)
        
        long_text = "This is sentence one. " * 500  # ~11k chars
        chunks = provider._chunk_transcript(long_text, chunk_size=10000)
        
        # Verify chunks don't exceed size
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 10500)  # Allow small margin
        
        # Verify chunks don't end mid-sentence
        for chunk in chunks:
            if chunk:
                self.assertTrue(
                    chunk.endswith('.') or chunk.endswith('!') or chunk.endswith('?'),
                    f"Chunk ends awkwardly: {chunk[-50:]}"
                )
    
    @patch('github_copilot_provider.Anthropic')
    def test_create_copilot_provider_factory(self, mock_anthropic):
        """Test factory function for creating providers."""
        provider = create_copilot_provider(self.test_config)
        
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, GitHubCopilotProvider)
        self.assertEqual(provider.model, "claude-3-5-sonnet-20241022")
    
    @patch('github_copilot_provider.Anthropic')
    def test_create_copilot_provider_missing_token(self, mock_anthropic):
        """Test factory with missing GitHub token."""
        bad_config = {"model": "claude-3-5-sonnet-20241022"}
        provider = create_copilot_provider(bad_config)
        
        self.assertIsNone(provider)
    
    @patch('github_copilot_provider.Anthropic')
    def test_generate_segments_returns_json_string(self, mock_anthropic):
        """Test that generate_segments returns valid JSON string."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"segments": [{"start_time": 10, "title": "Test"}]}')
        ]
        mock_client.messages.create.return_value = mock_response
        
        provider = GitHubCopilotProvider(github_token=self.valid_token)
        result = provider.generate_segments(
            system_prompt="Test system",
            transcript="Test transcript"
        )
        
        # Verify result is valid JSON
        parsed = json.loads(result)
        self.assertIn("segments", parsed)
        self.assertIsInstance(parsed["segments"], list)


class TestCleanJsonResponseCompatibility(unittest.TestCase):
    """Test that Claude responses are compatible with clean_json_response."""
    
    def test_clean_json_with_claude_format(self):
        """Test that clean_json_response can parse Claude-style JSON."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from create_viral_segments import clean_json_response
        
        # Simulated Claude response (well-formed JSON)
        claude_response = '''{
            "segments": [
                {
                    "start_text": "First words of segment",
                    "end_text": "Last words of segment",
                    "start_time_ref": "10s",
                    "title": "Viral Hook",
                    "reasoning": "This is viral because...",
                    "score": 95
                }
            ]
        }'''
        
        result = clean_json_response(claude_response)
        
        self.assertIn("segments", result)
        self.assertEqual(len(result["segments"]), 1)
        self.assertEqual(result["segments"][0]["score"], 95)
    
    def test_clean_json_with_claude_wrapped_json(self):
        """Test clean_json_response with Claude wrapping in markdown."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from create_viral_segments import clean_json_response
        
        # Claude sometimes wraps JSON in markdown blocks
        wrapped_response = '''```json
{
    "segments": [
        {
            "start_text": "First words",
            "title": "Test"
        }
    ]
}
```'''
        
        result = clean_json_response(wrapped_response)
        
        self.assertIn("segments", result)
        self.assertEqual(len(result["segments"]), 1)


if __name__ == '__main__':
    unittest.main()
