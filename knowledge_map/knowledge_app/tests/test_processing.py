import sys
import json
from unittest.mock import MagicMock, patch
from django.test import TestCase
from knowledge_app.processing import generate_knowledge_map_data

# Mock openai so it doesn't need to be installed in CI
sys.modules.setdefault('openai', MagicMock())


# =============================================================================
# Unit Tests for generate_knowledge_map_data()
# =============================================================================

class GenerateKnowledgeMapDataTests(TestCase):

    def _fake_response(self, topics=None, relationships=None):
        """Helper: build a mock OpenAI response with valid JSON output."""
        if topics is None:
            topics = [
                {
                    "label": "Machine Learning",
                    "summary": "A field of AI focused on learning from data.",
                    "keywords": ["neural", "network", "training"]
                }
            ]
        if relationships is None:
            relationships = [
                {
                    "source": "Machine Learning",
                    "target": "Data Science",
                    "label": "underpins"
                }
            ]
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "topics": topics,
            "relationships": relationships
        })
        return mock_response

    @patch("knowledge_app.processing.OpenAI")
    def test_returns_tuple_of_topics_and_relationships(self, MockOpenAI):
        """Function should return a tuple of (topics, relationships)."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        topics, relationships = generate_knowledge_map_data(
            "Some text about machine learning.")
        self.assertIsInstance(topics, list)
        self.assertIsInstance(relationships, list)

    @patch("knowledge_app.processing.OpenAI")
    def test_topics_have_required_keys(self, MockOpenAI):
        """Each topic must have label, summary and keywords keys."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        topics, _ = generate_knowledge_map_data("Some text.")
        for topic in topics:
            self.assertIn("label", topic)
            self.assertIn("summary", topic)
            self.assertIn("keywords", topic)

    @patch("knowledge_app.processing.OpenAI")
    def test_relationships_have_required_keys(self, MockOpenAI):
        """Each relationship must have source, target and label keys."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        _, relationships = generate_knowledge_map_data("Some text.")
        for rel in relationships:
            self.assertIn("source", rel)
            self.assertIn("target", rel)
            self.assertIn("label", rel)

    @patch("knowledge_app.processing.OpenAI")
    def test_returns_correct_number_of_topics(self, MockOpenAI):
        """The number of topics returned should match the JSON response."""
        topics_data = [
            {"label": f"Topic {i}",
                "summary": f"Summary {i}.", "keywords": ["kw"]}
            for i in range(4)
        ]
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response(
            topics=topics_data)
        MockOpenAI.return_value = mock_client

        topics, _ = generate_knowledge_map_data("Some text.")
        self.assertEqual(len(topics), 4)

    @patch("knowledge_app.processing.OpenAI")
    def test_returns_correct_number_of_relationships(self, MockOpenAI):
        """The number of relationships returned should match the JSON response."""
        relationships_data = [
            {"source": "A", "target": "B", "label": "causes"},
            {"source": "B", "target": "C", "label": "leads to"},
        ]
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response(
            relationships=relationships_data
        )
        MockOpenAI.return_value = mock_client

        _, relationships = generate_knowledge_map_data("Some text.")
        self.assertEqual(len(relationships), 2)

    @patch("knowledge_app.processing.OpenAI")
    def test_api_called_exactly_once(self, MockOpenAI):
        """OpenAI API should be called exactly once per invocation."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        generate_knowledge_map_data("Some text.")
        mock_client.responses.create.assert_called_once()

    @patch("knowledge_app.processing.OpenAI")
    def test_prompt_contains_text(self, MockOpenAI):
        """The prompt sent to OpenAI should include the input text."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        generate_knowledge_map_data("Unique text about climate change.")
        call_args = mock_client.responses.create.call_args
        self.assertIn("climate change", call_args[1]["input"])

    @patch("knowledge_app.processing.OpenAI")
    def test_handles_json_with_code_fences(self, MockOpenAI):
        """Should correctly strip markdown code fences from the response."""
        mock_response = MagicMock()
        mock_response.output_text = "```json\n" + json.dumps({
            "topics": [{"label": "AI", "summary": "About AI.", "keywords": ["ai"]}],
            "relationships": []
        }) + "\n```"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = mock_response
        MockOpenAI.return_value = mock_client

        topics, relationships = generate_knowledge_map_data("Some text.")
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0]["label"], "AI")

    @patch("knowledge_app.processing.OpenAI")
    def test_empty_relationships_list(self, MockOpenAI):
        """Should handle a response with no relationships gracefully."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response(
            relationships=[])
        MockOpenAI.return_value = mock_client

        _, relationships = generate_knowledge_map_data("Some text.")
        self.assertEqual(relationships, [])

    @patch("knowledge_app.processing.OpenAI")
    def test_topic_label_is_string(self, MockOpenAI):
        """Topic labels must be strings."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        topics, _ = generate_knowledge_map_data("Some text.")
        for topic in topics:
            self.assertIsInstance(topic["label"], str)

    @patch("knowledge_app.processing.OpenAI")
    def test_topic_keywords_is_list(self, MockOpenAI):
        """Topic keywords must be a list."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_response()
        MockOpenAI.return_value = mock_client

        topics, _ = generate_knowledge_map_data("Some text.")
        for topic in topics:
            self.assertIsInstance(topic["keywords"], list)
