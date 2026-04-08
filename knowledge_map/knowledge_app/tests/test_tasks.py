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