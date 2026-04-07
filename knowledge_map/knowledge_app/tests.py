from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UploadedFile
from unittest.mock import patch, MagicMock
import os
import sys

# Mock heavy dependencies so they don't need to be installed in CI
sys.modules['bertopic'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.feature_extraction'] = MagicMock()
sys.modules['sklearn.feature_extraction.text'] = MagicMock()
sys.modules['openai'] = MagicMock()

from knowledge_app.processing import extract_topics, generate_labels, generate_relationships


#----------------Tests for Authentication---------------------
class AuthenticationTests(TestCase):
    
    def setUp(self):
        # set up test user before each run
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    #-----------Login tests------------------------------------
    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    #------------------Login with valid user and password-------
    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    #-------------------Test Invalid password------------------
    def test_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # -------------------Logout test----------------------------
    def test_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

# Testing for navigation bar
class NavbarTest(TestCase):
    def setUp(self):
        self.client = Client()

    # Test all navbar links return 200
    def test_homepage_link(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)

    def test_maps_link(self):
        response = self.client.get(reverse('maps'))
        self.assertEqual(response.status_code, 200)

    def test_quiz_link(self):
        response = self.client.get(reverse('maps'))
        self.assertEqual(response.status_code, 200)

    def test_progress_link(self):
        response = self.client.get(reverse('maps'))
        self.assertEqual(response.status_code, 200)

    # Test navbar is included in base template
    def test_sidebar_present_in_page(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, 'id="sidebar"')

    def test_toggle_button_present(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, 'id="toggle-btn"')

    # Test navbar links are present
    def test_navbar_contains_all_links(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, reverse('homepage'))
        self.assertContains(response, reverse('maps'))
        self.assertContains(response, reverse('quiz'))
        self.assertContains(response, reverse('progress'))

    # Test navbar labels are present
    def test_navbar_labels(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Maps')
        self.assertContains(response, 'Quiz')
        self.assertContains(response, 'Progress')

    # Test navbar is on every page
    def test_sidebar_present_on_all_pages(self):
        pages = ['homepage', 'maps', 'quiz', 'progress']
        for page in pages:
            response = self.client.get(reverse(page))
            self.assertContains(response, 'id="sidebar"', msg_prefix=f"Sidebar missing on {page}")
            self.assertContains(response, 'id="toggle-btn"', msg_prefix=f"Toggle button missing on {page}")

# ----------------Tests for Upload Feature---------------------
class UploadPageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
    def setUp(self):
        self.client = Client()

    # Test upload page loads correctly
    def test_upload_page_loads(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)

    # Test upload page uses correct template
    def test_upload_page_uses_correct_template(self):
        response = self.client.get(reverse('upload'))
        self.assertTemplateUsed(response, 'knowledge_app/upload.html')

    # Test a valid PDF can be uploaded
    def test_valid_pdf_upload(self):
        pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        response = self.client.post(reverse('upload'), {'pdf_file': pdf})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.objects.count(), 1)

    # Test a non-PDF file is rejected
    def test_non_pdf_upload_rejected(self):
        txt = SimpleUploadedFile("test.txt", b"not a pdf", content_type="text/plain")
        response = self.client.post(reverse('upload'), {'pdf_file': txt})
        self.assertEqual(UploadedFile.objects.count(), 0)

    # Test uploaded files appear in the list
    def test_uploaded_files_appear_in_list(self):
        pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.client.post(reverse('upload'), {'pdf_file': pdf})
        response = self.client.get(reverse('upload'))
        self.assertContains(response, "test.pdf")

    # Test empty upload form does nothing
    def test_empty_upload_does_nothing(self):
        response = self.client.post(reverse('upload'), {})
        self.assertEqual(UploadedFile.objects.count(), 0)

    # Test model stores correct filename
    def test_model_stores_filename(self):
        pdf = SimpleUploadedFile("myfile.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.client.post(reverse('upload'), {'pdf_file': pdf})
        uploaded = UploadedFile.objects.first()
        self.assertIn("myfile.pdf", uploaded.file.name)

    # Clean up uploaded test files after tests run
    def tearDown(self):
        for f in UploadedFile.objects.all():
            if os.path.exists(f.file.path):
                os.remove(f.file.path)
# ----------------Tests for Delete Feature---------------------
class DeleteFileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def setUp(self):
        self.client = Client()  # set up fake browser before each test

    # Test deleting a file removes it from the database
    def test_delete_removes_file_from_database(self):
        pdf = SimpleUploadedFile("delete_me.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.client.post(reverse('upload'), {'pdf_file': pdf})  # upload a file
        uploaded = UploadedFile.objects.first()  # grab it from the database
        self.client.post(reverse('delete_file', args=[uploaded.id]))  # delete it
        self.assertEqual(UploadedFile.objects.count(), 0)  # confirm it's gone

    # Test deleting a file that doesn't exist returns 404
    def test_delete_nonexistent_file_returns_404(self):
        response = self.client.post(reverse('delete_file', args=[999]))  # try to delete something that doesn't exist
        self.assertEqual(response.status_code, 404)  # confirm we get a 404 instead of a crash

    # Clean up any leftover files after tests run
    def tearDown(self):
        for f in UploadedFile.objects.all():
            if os.path.exists(f.file.path):
                os.remove(f.file.path)

# =============================================================================
# Unit Tests for extract_topics()
# =============================================================================
 
class ExtractTopicsUnitTests(TestCase):
 
    # -------------------------------------------------------------------------
    # Input validation
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
        This test confirms the filter works by passing only short sentences so
        the function hits the 'not enough text' guard.
        """
        # Each sentence is under 10 chars so they'll all be filtered out
        text = "Hi. Ok. Yes. No. Go. Run. Jump. Skip. Stop. Done."
        result, error = extract_topics(text)
        self.assertIsNone(result)
 
    # -------------------------------------------------------------------------
    # Normal operation (BERTopic mocked so tests don't need GPU/transformers)
    # -------------------------------------------------------------------------
 
    @patch("knowledge_app.processing.BERTopic")
    def test_returns_list_on_valid_text(self, MockBERTopic):
        """With enough text, extract_topics should return a list and no error."""
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0, 0, 0, 1, 1, 1, 0, 1, 0, 1], None)
        mock_model.get_topic_info.return_value = _fake_topic_info()
        mock_model.get_topic.side_effect = lambda tid: [("word1", 0.9), ("word2", 0.8)]
        MockBERTopic.return_value = mock_model
 
        text = _long_text(15)
        result, error = extract_topics(text)
 
        self.assertIsNone(error)
        self.assertIsInstance(result, list)
 
    @patch("knowledge_app.processing.BERTopic")
    def test_result_contains_required_keys(self, MockBERTopic):
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
 
    @patch("knowledge_app.processing.BERTopic")
    def test_outlier_topic_minus_one_is_excluded(self, MockBERTopic):
        """Topic id -1 (BERTopic outlier bucket) must never appear in results."""
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([-1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], None)
        mock_model.get_topic_info.return_value = _fake_topic_info(topic_ids=[-1, 0])
        mock_model.get_topic.return_value = [("word", 0.9)]
        MockBERTopic.return_value = mock_model
 
        result, error = extract_topics(_long_text(15))
 
        topic_ids = [t["topic_id"] for t in result]
        self.assertNotIn(-1, topic_ids)
 
    @patch("knowledge_app.processing.BERTopic")
    def test_sentences_per_topic_capped_at_five(self, MockBERTopic):
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
 
    @patch("knowledge_app.processing.BERTopic")
    def test_keywords_are_strings(self, MockBERTopic):
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
 
    @patch("knowledge_app.processing.OpenAI")
    def test_returns_same_number_of_topics(self, MockOpenAI):
        """Output list length must equal input list length."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client
 
        topics = _fake_topics(3)
        result = generate_labels(topics)
        self.assertEqual(len(result), 3)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_label_and_summary_keys_added(self, MockOpenAI):
        """Each output topic must have 'label' and 'summary' keys."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response(
            "Climate Change Risks", "This topic covers extreme weather events."
        )
        MockOpenAI.return_value = mock_client
 
        result = generate_labels(_fake_topics(2))
 
        for topic in result:
            self.assertIn("label", topic)
            self.assertIn("summary", topic)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_label_is_correctly_parsed(self, MockOpenAI):
        """The label extracted from the API response should match the mock value."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response(
            label="Machine Learning Basics"
        )
        MockOpenAI.return_value = mock_client
 
        result = generate_labels(_fake_topics(1))
        self.assertEqual(result[0]["label"], "Machine Learning Basics")
 
    @patch("knowledge_app.processing.OpenAI")
    def test_summary_is_correctly_parsed(self, MockOpenAI):
        """The summary extracted from the API response should match the mock value."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response(
            summary="Neural networks learn from large datasets."
        )
        MockOpenAI.return_value = mock_client
 
        result = generate_labels(_fake_topics(1))
        self.assertEqual(result[0]["summary"], "Neural networks learn from large datasets.")
 
    @patch("knowledge_app.processing.OpenAI")
    def test_existing_topic_data_is_preserved(self, MockOpenAI):
        """Original topic keys (topic_id, keywords, sentences) must survive the merge."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client
 
        topics = _fake_topics(1)
        result = generate_labels(topics)
 
        self.assertIn("topic_id", result[0])
        self.assertIn("keywords", result[0])
        self.assertIn("sentences", result[0])
 
    @patch("knowledge_app.processing.OpenAI")
    def test_empty_topic_list_returns_empty_list(self, MockOpenAI):
        """Passing an empty list should return an empty list without calling the API."""
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
 
        result = generate_labels([])
 
        self.assertEqual(result, [])
        mock_client.responses.create.assert_not_called()
 
    @patch("knowledge_app.processing.OpenAI")
    def test_api_called_once_per_topic(self, MockOpenAI):
        """The OpenAI API should be called exactly once for each topic."""
        mock_client = MagicMock()
        mock_client.responses.create.return_value = self._fake_openai_response()
        MockOpenAI.return_value = mock_client
 
        n = 4
        generate_labels(_fake_topics(n))
        self.assertEqual(mock_client.responses.create.call_count, n)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_prompt_contains_keywords(self, MockOpenAI):
        """The prompt sent to OpenAI should include the topic's keywords."""
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
        mock_response.output_text = response_text  # ← was choices[0].message.content
        mock_client.responses.create.return_value = mock_response
        return mock_client
 
    @patch("knowledge_app.processing.OpenAI")
    def test_returns_list(self, MockOpenAI):
        """generate_relationships should always return a list."""
        MockOpenAI.return_value = self._mock_openai(
            "Climate Change -> Extreme Weather: causes\nExtreme Weather -> Migration: drives"
        )
        result = generate_relationships(_labeled_topics(2))
        self.assertIsInstance(result, list)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_relationship_has_required_keys(self, MockOpenAI):
        """Each relationship dict must have 'source', 'target', and 'label' keys."""
        MockOpenAI.return_value = self._mock_openai(
            "Topic A -> Topic B: influences"
        )
        result = generate_relationships(_labeled_topics(2))
 
        for rel in result:
            self.assertIn("source", rel)
            self.assertIn("target", rel)
            self.assertIn("label", rel)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_source_and_target_are_parsed_correctly(self, MockOpenAI):
        """Source and target values should come from the left and right of '->'."""
        MockOpenAI.return_value = self._mock_openai(
            "Machine Learning -> Data Science: underpins"
        )
        result = generate_relationships(_labeled_topics(2))
 
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "Machine Learning")
        self.assertEqual(result[0]["target"], "Data Science")
        self.assertEqual(result[0]["label"], "underpins")
 
    @patch("knowledge_app.processing.OpenAI")
    def test_multiple_relationships_parsed(self, MockOpenAI):
        """All valid lines in the response should be parsed into relationships."""
        MockOpenAI.return_value = self._mock_openai(
            "A -> B: causes\nB -> C: leads to\nA -> C: directly impacts"
        )
        result = generate_relationships(_labeled_topics(3))
        self.assertEqual(len(result), 3)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_lines_without_arrow_are_skipped(self, MockOpenAI):
        """Lines that don't match the expected format should be silently ignored."""
        MockOpenAI.return_value = self._mock_openai(
            "Here are the relationships:\nA -> B: causes\nThis line has no arrow."
        )
        result = generate_relationships(_labeled_topics(2))
        # Only the valid line should be parsed
        self.assertEqual(len(result), 1)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_empty_response_returns_empty_list(self, MockOpenAI):
        """If the model returns no parseable lines, result should be an empty list."""
        MockOpenAI.return_value = self._mock_openai("No relationships found.")
        result = generate_relationships(_labeled_topics(2))
        self.assertEqual(result, [])
 
    @patch("knowledge_app.processing.OpenAI")
    def test_all_topic_labels_included_in_prompt(self, MockOpenAI):
        """Every topic label should appear in the prompt sent to the API."""
        mock_client = self._mock_openai("A -> B: causes")
        MockOpenAI.return_value = mock_client
 
        topics = _labeled_topics(3)
        generate_relationships(topics)
 
        call_args = mock_client.responses.create.call_args
        prompt_content = call_args[1]["input"]
        for topic in topics:
            self.assertIn(topic["label"], prompt_content)
 
    @patch("knowledge_app.processing.OpenAI")
    def test_api_called_exactly_once(self, MockOpenAI):
        """generate_relationships should make exactly one API call."""
        mock_client = self._mock_openai("A -> B: causes")
        MockOpenAI.return_value = mock_client
 
        generate_relationships(_labeled_topics(4))
        mock_client.responses.create.assert_called_once()

 
 
# =============================================================================
# Integration Tests (pipeline: extract -> label -> relate)
# =============================================================================
 
class TopicsPipelineIntegrationTests(TestCase):
    """
    Tests that simulate the full pipeline without real ML models or API calls.
    All external dependencies are mocked so tests are fast and deterministic.
    """
 
    @patch("knowledge_app.processing.OpenAI")
    @patch("knowledge_app.processing.BERTopic")
    def test_full_pipeline_returns_labeled_topics_and_relationships(
        self, MockBERTopic, MockOpenAI
    ):
        """End-to-end: text -> topics -> labels -> relationships all succeeds."""
 
        # Mock BERTopic
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1], None)
        mock_model.get_topic_info.return_value = _fake_topic_info(topic_ids=[0, 1])
        mock_model.get_topic.return_value = [("climate", 0.9), ("change", 0.8)]
        MockBERTopic.return_value = mock_model
 
        # Mock OpenAI (2 label calls + 1 relationships call)
        mock_client = MagicMock()
        label_response = MagicMock()
        label_response.output_text = "Label: Climate Topics\nSummary: Topics about climate."
        rel_response = MagicMock()
        rel_response.output_text = "Climate Topics -> Migration: drives"
        mock_client.responses.create.side_effect = [
            label_response, label_response, rel_response
        ]
        MockOpenAI.return_value = mock_client
 
        # Run the full pipeline
        topics, error = extract_topics(_long_text(12))
        self.assertIsNone(error)
        self.assertIsInstance(topics, list)
 
        labeled = generate_labels(topics)
        self.assertEqual(len(labeled), len(topics))
        self.assertIn("label", labeled[0])
 
        relationships = generate_relationships(labeled)
        self.assertIsInstance(relationships, list)
 
    @patch("knowledge_app.processing.OpenAI")
    @patch("knowledge_app.processing.BERTopic")
    def test_pipeline_handles_single_topic_gracefully(self, MockBERTopic, MockOpenAI):
        """A document that produces only one topic should still flow through the pipeline."""
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
 
    @patch("knowledge_app.processing.OpenAI")
    @patch("knowledge_app.processing.BERTopic")
    def test_pipeline_short_text_stops_early(self, MockBERTopic, MockOpenAI):
        """Short text should stop at extract_topics and never call the API."""
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
 
        result, error = extract_topics("Too short.")
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        mock_client.chat.completions.create.assert_not_called()

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
    """Return a list of dicts that mimics BERTopic's get_topic_info() output."""
    if topic_ids is None:
        topic_ids = [0]
    
    # Create a simple object that mimics pandas DataFrame's iterrows()
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

from django.test import TestCase
from unittest.mock import patch, MagicMock
from knowledge_app.tasks import generate_knowledge_map
from knowledge_app.models import KnowledgeMap, TopicNode, NodeRelationship


# =============================================================================
# Helpers
# =============================================================================

def _make_knowledge_map(status='pending', extracted_text='some text'):
    """
    Return a MagicMock that behaves like a KnowledgeMap instance.
    Using a mock avoids needing a real database for unit tests.
    """
    km = MagicMock(spec=KnowledgeMap)
    km.id = 1
    km.status = status
    km.uploaded_file.extracted_text = extracted_text
    return km


def _fake_labeled_topics():
    return [
        {
            'topic_id': 0,
            'label': 'Machine Learning',
            'summary': 'Covers ML algorithms.',
            'keywords': ['model', 'train'],
            'sentences': ['Models are trained on data.'],
        },
        {
            'topic_id': 1,
            'label': 'Data Science',
            'summary': 'Covers data analysis.',
            'keywords': ['data', 'analysis'],
            'sentences': ['Data is cleaned and analysed.'],
        },
    ]


def _fake_relationships():
    return [
        {'source': 'Machine Learning', 'target': 'Data Science', 'label': 'underpins'},
    ]


# =============================================================================
# Unit Tests
# =============================================================================

class GenerateKnowledgeMapUnitTests(TestCase):

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_status_set_to_complete_on_success(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """Status should be 'complete' after a successful run."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = _fake_relationships()
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertEqual(km.status, 'complete')

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_returns_success_message_containing_map_id(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """Task should return a success string that includes the knowledge map id."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = _fake_relationships()
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        result = generate_knowledge_map(1)

        self.assertIn('1', result)
        self.assertIn('successfully', result.lower())

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_status_is_processing_before_complete(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """
        Status should be 'processing' before pipeline work begins
        and 'complete' after all steps finish.
        """
        status_log = []
        km = _make_knowledge_map()
        mock_get.return_value = km

        def record_status():
            status_log.append(km.status)

        km.save.side_effect = record_status
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertEqual(status_log[0], 'processing')
        self.assertEqual(status_log[-1], 'complete')

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_save_called_at_least_twice_on_success(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """km.save() must be called at least twice: once for 'processing', once for 'complete'."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertGreaterEqual(km.save.call_count, 2)

    # ------------------------------------------------------------------
    # Pipeline call ordering
    # ------------------------------------------------------------------

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_extract_topics_called_with_pdf_text(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """extract_topics must receive the text extracted from the uploaded PDF."""
        km = _make_knowledge_map(extracted_text='my pdf text here')
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        mock_extract.assert_called_once_with('my pdf text here')

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_generate_labels_receives_output_of_extract_topics(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """generate_labels should be called with the topics returned by extract_topics."""
        raw_topics = _fake_labeled_topics()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (raw_topics, None)
        mock_labels.return_value = raw_topics
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock() for _ in raw_topics]

        generate_knowledge_map(1)

        mock_labels.assert_called_once_with(raw_topics)

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_generate_relationships_receives_output_of_generate_labels(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """generate_relationships should be called with the output of generate_labels."""
        labeled = _fake_labeled_topics()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (labeled, None)
        mock_labels.return_value = labeled
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock() for _ in labeled]

        generate_knowledge_map(1)

        mock_rels.assert_called_once_with(labeled)

    # ------------------------------------------------------------------
    # TopicNode creation
    # ------------------------------------------------------------------

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_topic_node_created_for_each_labeled_topic(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """A TopicNode should be created for every labeled topic returned."""
        topics = _fake_labeled_topics()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (topics, None)
        mock_labels.return_value = topics
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock() for _ in topics]

        generate_knowledge_map(1)

        self.assertEqual(mock_create_node.call_count, len(topics))

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_topic_node_created_with_correct_fields(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """TopicNode.objects.create must receive label, summary, and knowledge_map."""
        topics = _fake_labeled_topics()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (topics, None)
        mock_labels.return_value = topics
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock() for _ in topics]

        generate_knowledge_map(1)

        first_call = mock_create_node.call_args_list[0].kwargs
        self.assertEqual(first_call['label'], 'Machine Learning')
        self.assertEqual(first_call['summary'], 'Covers ML algorithms.')
        self.assertEqual(first_call['knowledge_map'], km)

    # ------------------------------------------------------------------
    # NodeRelationship creation
    # ------------------------------------------------------------------

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_relationship_created_with_correct_fields(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """NodeRelationship.objects.create must receive source, target, label, and map."""
        topics = _fake_labeled_topics()
        source_node = MagicMock()
        target_node = MagicMock()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (topics, None)
        mock_labels.return_value = topics
        mock_rels.return_value = _fake_relationships()
        mock_create_node.side_effect = [source_node, target_node]

        generate_knowledge_map(1)

        mock_create_rel.assert_called_once_with(
            knowledge_map=km,
            source_topic=source_node,
            target_topic=target_node,
            relationship_label='underpins',
        )

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_multiple_relationships_all_created(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """All valid relationships returned by generate_relationships should be saved."""
        topics = _fake_labeled_topics()
        node_a, node_b = MagicMock(), MagicMock()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (topics, None)
        mock_labels.return_value = topics
        mock_rels.return_value = [
            {'source': 'Machine Learning', 'target': 'Data Science', 'label': 'underpins'},
            {'source': 'Data Science', 'target': 'Machine Learning', 'label': 'feeds into'},
        ]
        mock_create_node.side_effect = [node_a, node_b]

        generate_knowledge_map(1)

        self.assertEqual(mock_create_rel.call_count, 2)

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_relationship_skipped_when_source_node_missing(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """A relationship whose source label has no matching node should be silently skipped."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = [
            {'source': 'Nonexistent Topic', 'target': 'Data Science', 'label': 'causes'}
        ]
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        mock_create_rel.assert_not_called()

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_relationship_skipped_when_target_node_missing(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """A relationship whose target label has no matching node should be silently skipped."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = [
            {'source': 'Machine Learning', 'target': 'Nonexistent Topic', 'label': 'causes'}
        ]
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        mock_create_rel.assert_not_called()

    @patch('knowledge_app.tasks.NodeRelationship.objects.create')
    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_no_relationships_still_completes_successfully(
        self, mock_get, mock_extract, mock_labels, mock_rels,
        mock_create_node, mock_create_rel
    ):
        """The task should complete successfully even when there are no relationships."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = []
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        result = generate_knowledge_map(1)

        self.assertEqual(km.status, 'complete')
        self.assertIn('successfully', result.lower())
        mock_create_rel.assert_not_called()

    # ------------------------------------------------------------------
    # Failure paths
    # ------------------------------------------------------------------

    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_extract_topics_error_sets_status_to_failed(self, mock_get, mock_extract):
        """When extract_topics returns an error string, status must be set to 'failed'."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (None, 'Not enough text to generate topics')

        generate_knowledge_map(1)

        self.assertEqual(km.status, 'failed')

    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_extract_topics_error_returns_error_message(self, mock_get, mock_extract):
        """When extract_topics fails, the task should return the error string directly."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (None, 'Not enough text to generate topics')

        result = generate_knowledge_map(1)

        self.assertEqual(result, 'Not enough text to generate topics')

    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_extract_topics_error_saves_failed_status(self, mock_get, mock_extract):
        """km.save() must be called after setting status to 'failed' on extract error."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (None, 'Not enough text to generate topics')

        generate_knowledge_map(1)

        km.save.assert_called()

    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_exception_in_generate_labels_sets_status_to_failed(
        self, mock_get, mock_extract, mock_labels
    ):
        """An unexpected exception during generate_labels should set status to 'failed'."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.side_effect = RuntimeError('OpenAI API is down')

        generate_knowledge_map(1)

        self.assertEqual(km.status, 'failed')

    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_exception_message_returned_as_string(
        self, mock_get, mock_extract, mock_labels
    ):
        """The string form of any unhandled exception should be returned by the task."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.side_effect = RuntimeError('OpenAI API is down')

        result = generate_knowledge_map(1)

        self.assertEqual(result, 'OpenAI API is down')

    @patch('knowledge_app.tasks.TopicNode.objects.create')
    @patch('knowledge_app.tasks.generate_relationships')
    @patch('knowledge_app.tasks.generate_labels')
    @patch('knowledge_app.tasks.extract_topics')
    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_exception_during_db_write_sets_status_to_failed(
        self, mock_get, mock_extract, mock_labels, mock_rels, mock_create_node
    ):
        """A database error when creating a TopicNode should mark the map as failed."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_extract.return_value = (_fake_labeled_topics(), None)
        mock_labels.return_value = _fake_labeled_topics()
        mock_rels.return_value = []
        mock_create_node.side_effect = Exception('DB constraint violation')

        generate_knowledge_map(1)

        self.assertEqual(km.status, 'failed')

    # ------------------------------------------------------------------
    # Bug fix: KnowledgeMap.DoesNotExist no longer crashes the worker
    # ------------------------------------------------------------------

    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_knowledge_map_not_found_does_not_raise(self, mock_get):
        """
        If KnowledgeMap.objects.get() raises DoesNotExist, the task should
        return an error string rather than crashing with an UnboundLocalError.
        The fix: knowledge_map = None before the try block.
        """
        mock_get.side_effect = KnowledgeMap.DoesNotExist('No KnowledgeMap matches id=999')

        try:
            result = generate_knowledge_map(999)
        except UnboundLocalError:
            self.fail(
                "UnboundLocalError raised — knowledge_map was referenced before assignment. "
                "Ensure knowledge_map = None is set before the try block."
            )

        self.assertIsInstance(result, str)

    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_knowledge_map_not_found_returns_error_string(self, mock_get):
        """When the map doesn't exist, the returned value should be a non-empty string."""
        mock_get.side_effect = KnowledgeMap.DoesNotExist('No KnowledgeMap matches id=999')

        result = generate_knowledge_map(999)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch('knowledge_app.tasks.KnowledgeMap.objects.get')
    def test_knowledge_map_not_found_does_not_attempt_save(self, mock_get):
        """
        When DoesNotExist is raised, knowledge_map is None so no .save()
        should be attempted. The fix: guard with 'if knowledge_map is not None'
        in the except block.
        """
        mock_get.side_effect = KnowledgeMap.DoesNotExist('No KnowledgeMap matches id=999')

        try:
            generate_knowledge_map(999)
        except AttributeError:
            self.fail(
                "AttributeError raised — task tried to call .save() on None. "
                "Check the 'if knowledge_map is not None' guard in the except block."
            )

#===============views.py create_map and view_map and map_status testing=======================================
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

from knowledge_app.models import UploadedFile, KnowledgeMap
from knowledge_app.tasks import generate_knowledge_map


class CreateMapViewTest(TestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Create a sample uploaded file
        self.uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile("test.pdf", b"Dummy content", content_type="application/pdf"),
            uploaded_at="2024-01-01"
        )

    def test_create_map_get(self):
        """GET request should return 200 and include uploaded files in context"""
        response = self.client.get(reverse('create_map'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'knowledge_app/create_map.html')
        self.assertIn('files', response.context)
        self.assertIn(self.uploaded_file, response.context['files'])

    @patch('knowledge_app.views.generate_knowledge_map.delay')
    def test_create_map_post_creates_map_and_triggers_task(self, mock_delay):
        """POST request should create a KnowledgeMap and call the Celery task"""
        response = self.client.post(reverse('create_map'), {
            'file_id': self.uploaded_file.id,
            'title': 'Test Map'
        })

        # Check that the map was created
        self.assertEqual(KnowledgeMap.objects.count(), 1)
        km = KnowledgeMap.objects.first()
        self.assertEqual(km.title, 'Test Map')
        self.assertEqual(km.status, 'pending')
        self.assertEqual(km.user, self.user)
        self.assertEqual(km.uploaded_file, self.uploaded_file)

        # Check that the Celery task was called with the correct map ID
        mock_delay.assert_called_once_with(km.id)

        # Check redirect to the view_map page
        self.assertRedirects(response, reverse('view_map', args=[km.id]))

    def test_create_map_requires_login(self):
        """Anonymous users should be redirected to login page"""
        self.client.logout()
        response = self.client.get(reverse('create_map'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("create_map")}')