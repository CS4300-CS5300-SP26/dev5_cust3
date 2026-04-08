import sys
from unittest.mock import MagicMock, patch

# Must mock BEFORE importing processing.py so the imports inside it don't crash
sys.modules.setdefault('bertopic', MagicMock())
sys.modules.setdefault('sentence_transformers', MagicMock())

# sklearn needs to be mocked as a hierarchy
sklearn_mock = MagicMock()
sys.modules.setdefault('sklearn', sklearn_mock)
sys.modules.setdefault('sklearn.feature_extraction', sklearn_mock.feature_extraction)
sys.modules.setdefault('sklearn.feature_extraction.text', sklearn_mock.feature_extraction.text)

sys.modules.setdefault('openai', MagicMock())

from django.test import TestCase
from knowledge_app.processing import extract_topics, generate_labels, generate_relationships


# =============================================================================
# Unit Tests for extract_topics()
# =============================================================================

class ExtractTopicsUnitTests(TestCase):

    # -------------------------------------------------------------------------
    # Input validation - these don't need mocks, they fail before BERTopic runs
    # -------------------------------------------------------------------------

    def test_returns_error_when_text_is_too_short(self):
        """Fewer than 10 sentences should return None and an error message."""
        short_text = "Hello world. This is short."
        result, error = extract_topics(short_text)
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    def test_returns_error_message_string(self):
        """The error returned for short text should be a non-empty string."""
        result, error = extract_topics("Too short.")
        self.assertIsInstance(error, str)
        self.assertGreater(len(error), 0)

    def test_empty_string_returns_error(self):
        """An empty string should be treated as insufficient text."""
        result, error = extract_topics("")
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    def test_sentences_are_split_correctly(self):
        """
        Sentences shorter than 10 chars are filtered out before BERTopic runs.
        Passing only short sentences means the function hits the guard clause.
        """
        text = "Hi. Ok. Yes. No. Go. Run. Jump. Skip. Stop. Done."
        result, error = extract_topics(text)
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    # -------------------------------------------------------------------------
    # Normal operation — patch BERTopic and CountVectorizer inside processing
    # -------------------------------------------------------------------------

    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.BERTopic")
    def test_returns_list_on_valid_text(self, MockBERTopic, MockCountVectorizer):
        """With enough text, extract_topics should return a list and no error."""
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0], None)
        mock_model.get_topic_info.return_value = _fake_topic_info()
        mock_model.get_topic.side_effect = lambda tid: [("word1", 0.9), ("word2", 0.8)]
        MockBERTopic.return_value = mock_model

        result, error = extract_topics(_long_text(15))

        self.assertIsNone(error)
        self.assertIsInstance(result, list)

    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.BERTopic")
    def test_result_contains_required_keys(self, MockBERTopic, MockCountVectorizer):
        """Each topic dict must have topic_id, keywords, and sentences keys."""
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0] * 15, None)
        mock_model.get_topic_info.return_value = _fake_topic_info()
        mock_model.get_topic.return_value = [("alpha", 0.9), ("beta", 0.7)]
        MockBERTopic.return_value = mock_model

        result, error = extract_topics(_long_text(15))

        self.assertIsNone(error)
        for topic in result:
            self.assertIn("topic_id", topic)
            self.assertIn("keywords", topic)
            self.assertIn("sentences", topic)

    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.BERTopic")
    def test_outlier_topic_minus_one_is_excluded(self, MockBERTopic, MockCountVectorizer):
        """Topic id -1 (BERTopic outlier bucket) must never appear in results."""
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([-1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], None)
        mock_model.get_topic_info.return_value = _fake_topic_info(topic_ids=[-1, 0])
        mock_model.get_topic.return_value = [("word", 0.9)]
        MockBERTopic.return_value = mock_model

        result, error = extract_topics(_long_text(15))

        topic_ids = [t["topic_id"] for t in result]
        self.assertNotIn(-1, topic_ids)

    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.BERTopic")
    def test_sentences_per_topic_capped_at_five(self, MockBERTopic, MockCountVectorizer):
        """At most 5 sentences should be kept per topic."""
        n_docs = 20
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0] * n_docs, None)
        mock_model.get_topic_info.return_value = _fake_topic_info()
        mock_model.get_topic.return_value = [("kw", 0.9)]
        MockBERTopic.return_value = mock_model

        result, error = extract_topics(_long_text(n_docs))

        for topic in result:
            self.assertLessEqual(len(topic["sentences"]), 5)

    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.BERTopic")
    def test_keywords_are_strings(self, MockBERTopic, MockCountVectorizer):
        """Keywords list must contain plain strings, not tuples."""
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0] * 12, None)
        mock_model.get_topic_info.return_value = _fake_topic_info()
        mock_model.get_topic.return_value = [("machine", 0.95), ("learning", 0.85)]
        MockBERTopic.return_value = mock_model

        result, _ = extract_topics(_long_text(12))

        for topic in result:
            for kw in topic["keywords"]:
                self.assertIsInstance(kw, str)


# =============================================================================
# Unit Tests for generate_labels()
# =============================================================================

class GenerateLabelsUnitTests(TestCase):

    def _fake_openai_response(self, label="Test Label", summary="Test summary sentence."):
        """Helper: build a minimal mock that looks like an OpenAI chat response."""
        mock_response = MagicMock()
        mock_response.output_text = f"Label: {label}\nSummary: {summary}"
        return mock_response

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_returns_same_number_of_topics(self, MockOpenAI, MockSettings):
        """Output list length must equal input list length."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client

        result = generate_labels(_fake_topics(3))
        self.assertEqual(len(result), 3)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_label_and_summary_keys_added(self, MockOpenAI, MockSettings):
        """Each output topic must have 'label' and 'summary' keys."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response(
            "Climate Change Risks", "This topic covers extreme weather events."
        )
        MockOpenAI.return_value = mock_client

        result = generate_labels(_fake_topics(2))

        for topic in result:
            self.assertIn("label", topic)
            self.assertIn("summary", topic)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_label_is_correctly_parsed(self, MockOpenAI, MockSettings):
        """The label extracted from the API response should match the mock value."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response(
            label="Machine Learning Basics"
        )
        MockOpenAI.return_value = mock_client

        result = generate_labels(_fake_topics(1))
        self.assertEqual(result[0]["label"], "Machine Learning Basics")

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_summary_is_correctly_parsed(self, MockOpenAI, MockSettings):
        """The summary extracted from the API response should match the mock value."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response(
            summary="Neural networks learn from large datasets."
        )
        MockOpenAI.return_value = mock_client

        result = generate_labels(_fake_topics(1))
        self.assertEqual(result[0]["summary"], "Neural networks learn from large datasets.")

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_existing_topic_data_is_preserved(self, MockOpenAI, MockSettings):
        """Original topic keys (topic_id, keywords, sentences) must survive the merge."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client

        result = generate_labels(_fake_topics(1))

        self.assertIn("topic_id", result[0])
        self.assertIn("keywords", result[0])
        self.assertIn("sentences", result[0])

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_empty_topic_list_returns_empty_list(self, MockOpenAI, MockSettings):
        """Passing an empty list should return an empty list without calling the API."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        result = generate_labels([])

        self.assertEqual(result, [])
        mock_client.responses.create.assert_not_called()

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_api_called_once_per_topic(self, MockOpenAI, MockSettings):
        """The OpenAI API should be called exactly once for each topic."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client

        n = 4
        generate_labels(_fake_topics(n))
        self.assertEqual(mock_client.responses.create.call_count, n)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_prompt_contains_keywords(self, MockOpenAI, MockSettings):
        """The prompt sent to OpenAI should include the topic's keywords."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client

        topics = [{"topic_id": 0, "keywords": ["neural", "network"], "sentences": ["Networks learn."]}]
        generate_labels(topics)

        call_args = mock_client.responses.create.call_args
        prompt_content = call_args[1]["input"]
        self.assertIn("neural", prompt_content)
        self.assertIn("network", prompt_content)


# =============================================================================
# Unit Tests for generate_relationships()
# =============================================================================

class GenerateRelationshipsUnitTests(TestCase):

    def _mock_openai(self, response_text):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.output_text = response_text
        mock_client.responses.create.return_value = mock_response
        return mock_client

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_returns_list(self, MockOpenAI, MockSettings):
        """generate_relationships should always return a list."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai(
            "Climate Change -> Extreme Weather: causes\nExtreme Weather -> Migration: drives"
        )
        result = generate_relationships(_labeled_topics(2))
        self.assertIsInstance(result, list)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_relationship_has_required_keys(self, MockOpenAI, MockSettings):
        """Each relationship dict must have 'source', 'target', and 'label' keys."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai("Topic A -> Topic B: influences")
        result = generate_relationships(_labeled_topics(2))

        for rel in result:
            self.assertIn("source", rel)
            self.assertIn("target", rel)
            self.assertIn("label", rel)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_source_and_target_are_parsed_correctly(self, MockOpenAI, MockSettings):
        """Source and target values should come from the left and right of '->'."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai(
            "Machine Learning -> Data Science: underpins"
        )
        result = generate_relationships(_labeled_topics(2))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "Machine Learning")
        self.assertEqual(result[0]["target"], "Data Science")
        self.assertEqual(result[0]["label"], "underpins")

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_multiple_relationships_parsed(self, MockOpenAI, MockSettings):
        """All valid lines in the response should be parsed into relationships."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai(
            "A -> B: causes\nB -> C: leads to\nA -> C: directly impacts"
        )
        result = generate_relationships(_labeled_topics(3))
        self.assertEqual(len(result), 3)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_lines_without_arrow_are_skipped(self, MockOpenAI, MockSettings):
        """Lines that don't match the expected format should be silently ignored."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai(
            "Here are the relationships:\nA -> B: causes\nThis line has no arrow."
        )
        result = generate_relationships(_labeled_topics(2))
        self.assertEqual(len(result), 1)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_empty_response_returns_empty_list(self, MockOpenAI, MockSettings):
        """If the model returns no parseable lines, result should be an empty list."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai("No relationships found.")
        result = generate_relationships(_labeled_topics(2))
        self.assertEqual(result, [])

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_all_topic_labels_included_in_prompt(self, MockOpenAI, MockSettings):
        """Every topic label should appear in the prompt sent to the API."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = self._mock_openai("A -> B: causes")
        MockOpenAI.return_value = mock_client

        topics = _labeled_topics(3)
        generate_relationships(topics)

        call_args = mock_client.responses.create.call_args
        prompt_content = call_args[1]["input"]
        for topic in topics:
            self.assertIn(topic["label"], prompt_content)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_api_called_exactly_once(self, MockOpenAI, MockSettings):
        """generate_relationships should make exactly one API call."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = self._mock_openai("A -> B: causes")
        MockOpenAI.return_value = mock_client

        generate_relationships(_labeled_topics(4))
        mock_client.responses.create.assert_called_once()

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_empty_lines_are_skipped(self, MockOpenAI, MockSettings):
        """Empty lines in the response should not cause errors."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai(
            "A -> B: causes\n\n\nB -> C: leads to"
        )
        result = generate_relationships(_labeled_topics(2))
        self.assertEqual(len(result), 2)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    def test_malformed_line_missing_colon_is_skipped(self, MockOpenAI, MockSettings):
        """A line with -> but no colon should be skipped without crashing."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        MockOpenAI.return_value = self._mock_openai(
            "A -> B causes\nA -> B: valid"
        )
        result = generate_relationships(_labeled_topics(2))
        self.assertEqual(len(result), 1)


# =============================================================================
# Integration Tests (pipeline: extract -> label -> relate)
# =============================================================================

class TopicsPipelineIntegrationTests(TestCase):

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.OpenAI")
    @patch("knowledge_app.processing.BERTopic")
    def test_full_pipeline_returns_labeled_topics_and_relationships(
        self, MockBERTopic, MockOpenAI, MockCountVectorizer, MockSettings
    ):
        """End-to-end: text -> topics -> labels -> relationships all succeeds."""
        MockSettings.OPENAI_API_KEY = "fake-key"

        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1], None)
        mock_model.get_topic_info.return_value = _fake_topic_info(topic_ids=[0, 1])
        mock_model.get_topic.return_value = [("climate", 0.9), ("change", 0.8)]
        MockBERTopic.return_value = mock_model

        mock_client = MagicMock()
        label_response = MagicMock()
        label_response.output_text = "Label: Climate Topics\nSummary: Topics about climate."
        rel_response = MagicMock()
        rel_response.output_text = "Climate Topics -> Migration: drives"
        mock_client.responses.create.side_effect = [
            label_response, label_response, rel_response
        ]
        MockOpenAI.return_value = mock_client

        topics, error = extract_topics(_long_text(12))
        self.assertIsNone(error)
        self.assertIsInstance(topics, list)

        labeled = generate_labels(topics)
        self.assertEqual(len(labeled), len(topics))
        self.assertIn("label", labeled[0])

        relationships = generate_relationships(labeled)
        self.assertIsInstance(relationships, list)

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.CountVectorizer")
    @patch("knowledge_app.processing.OpenAI")
    @patch("knowledge_app.processing.BERTopic")
    def test_pipeline_handles_single_topic_gracefully(
        self, MockBERTopic, MockOpenAI, MockCountVectorizer, MockSettings
    ):
        """A document that produces only one topic should still flow through the pipeline."""
        MockSettings.OPENAI_API_KEY = "fake-key"

        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0] * 12, None)
        mock_model.get_topic_info.return_value = _fake_topic_info(topic_ids=[0])
        mock_model.get_topic.return_value = [("education", 0.9)]
        MockBERTopic.return_value = mock_model

        mock_client = MagicMock()
        label_resp = MagicMock()
        label_resp.output_text = "Label: Education\nSummary: About schooling."
        rel_resp = MagicMock()
        rel_resp.output_text = "No relationships."
        mock_client.responses.create.side_effect = [label_resp, rel_resp]
        MockOpenAI.return_value = mock_client

        topics, _ = extract_topics(_long_text(12))
        labeled = generate_labels(topics)
        relationships = generate_relationships(labeled)

        self.assertEqual(len(labeled), 1)
        self.assertEqual(relationships, [])

    @patch("knowledge_app.processing.settings")
    @patch("knowledge_app.processing.OpenAI")
    @patch("knowledge_app.processing.BERTopic")
    def test_pipeline_short_text_stops_early(self, MockBERTopic, MockOpenAI, MockSettings):
        """Short text should stop at extract_topics and never call the API."""
        MockSettings.OPENAI_API_KEY = "fake-key"
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        result, error = extract_topics("Too short.")
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        mock_client.responses.create.assert_not_called()


# =============================================================================
# Shared test helpers
# =============================================================================

def _long_text(n_sentences):
    """Generate text with n_sentences, each long enough to pass the length filter."""
    sentences = [
        f"This is a detailed sentence number {i} about an interesting topic in the document."
        for i in range(n_sentences)
    ]
    return ". ".join(sentences) + "."


def _fake_topic_info(topic_ids=None):
    """Return an object that mimics BERTopic's get_topic_info() DataFrame output."""
    if topic_ids is None:
        topic_ids = [0]

    class FakeDataFrame:
        def __init__(self, data):
            self.data = data

        def iterrows(self):
            for i, row in enumerate(self.data):
                yield i, row

    rows = [{"Topic": tid, "Count": 10} for tid in topic_ids]
    return FakeDataFrame(rows)


def _fake_topics(n):
    """Return n minimal topic dicts as produced by extract_topics."""
    return [
        {
            "topic_id": i,
            "keywords": ["word_a", "word_b", "word_c"],
            "sentences": [f"Example sentence {i} about the topic here."],
        }
        for i in range(n)
    ]


def _labeled_topics(n):
    """Return n topic dicts with label/summary as produced by generate_labels."""
    labels = ["Alpha Topic", "Beta Topic", "Gamma Topic", "Delta Topic"]
    return [
        {
            "topic_id": i,
            "keywords": ["word_a", "word_b"],
            "sentences": [f"Sentence {i}."],
            "label": labels[i % len(labels)],
            "summary": f"Summary for topic {i}.",
        }
        for i in range(n)
    ]