from django.test import TestCase
from unittest.mock import patch, MagicMock
from knowledge_app.tasks import generate_knowledge_map
from knowledge_app.models import KnowledgeMap, TopicNode, NodeRelationship

# =============================================================================
# Helpers
# =============================================================================


def _make_knowledge_map(status="pending", extracted_text="some text"):
    km = MagicMock(spec=KnowledgeMap)
    km.id = 1
    km.status = status
    km.uploaded_file.extracted_text = extracted_text
    return km


def _fake_topics():
    return [
        {
            "label": "Machine Learning",
            "summary": "Covers ML algorithms.",
            "keywords": ["model", "train"],
        },
        {
            "label": "Data Science",
            "summary": "Covers data analysis.",
            "keywords": ["data", "analysis"],
        },
    ]


def _fake_relationships():
    return [
        {"source": "Machine Learning", "target": "Data Science", "label": "underpins"},
    ]


# =============================================================================
# Unit Tests
# =============================================================================


class GenerateKnowledgeMapUnitTests(TestCase):

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_status_set_to_complete_on_success(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """Status should be 'complete' after a successful run."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), _fake_relationships())
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertEqual(km.status, "complete")

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_returns_success_message_containing_map_id(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """Task should return a success string that includes the knowledge map id."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), _fake_relationships())
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        result = generate_knowledge_map(1)

        self.assertIn("1", result)
        self.assertIn("successfully", result.lower())

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_status_is_processing_before_complete(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """Status should be 'processing' before pipeline work and 'complete' after."""
        status_log = []
        km = _make_knowledge_map()
        mock_get.return_value = km

        def record_status():
            status_log.append(km.status)

        km.save.side_effect = record_status
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertEqual(status_log[0], "processing")
        self.assertEqual(status_log[-1], "complete")

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_save_called_at_least_twice_on_success(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """km.save() must be called at least twice: once for 'processing', once for 'complete'."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertGreaterEqual(km.save.call_count, 2)

    # ------------------------------------------------------------------
    # Pipeline call
    # ------------------------------------------------------------------

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_generate_knowledge_map_data_called_with_pdf_text(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """generate_knowledge_map_data must receive the extracted PDF text."""
        km = _make_knowledge_map(extracted_text="my pdf text here")
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        mock_data.assert_called_once_with("my pdf text here")

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_generate_knowledge_map_data_called_exactly_once(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """generate_knowledge_map_data should only be called once per task run."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        mock_data.assert_called_once()

    # ------------------------------------------------------------------
    # TopicNode creation
    # ------------------------------------------------------------------

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_topic_node_created_for_each_topic(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """A TopicNode should be created for every topic returned."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        self.assertEqual(mock_create_node.call_count, len(_fake_topics()))

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_topic_node_created_with_correct_fields(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """TopicNode.objects.create must receive label, summary, and knowledge_map."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        first_call = mock_create_node.call_args_list[0].kwargs
        self.assertEqual(first_call["label"], "Machine Learning")
        self.assertEqual(first_call["summary"], "Covers ML algorithms.")
        self.assertEqual(first_call["knowledge_map"], km)

    # ------------------------------------------------------------------
    # NodeRelationship creation
    # ------------------------------------------------------------------

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_relationship_created_with_correct_fields(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """NodeRelationship.objects.create must receive source, target, label, and map."""
        source_node = MagicMock()
        target_node = MagicMock()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), _fake_relationships())
        mock_create_node.side_effect = [source_node, target_node]

        generate_knowledge_map(1)

        mock_create_rel.assert_called_once_with(
            knowledge_map=km,
            source_topic=source_node,
            target_topic=target_node,
            relationship_label="underpins",
        )

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_multiple_relationships_all_created(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """All valid relationships should be saved."""
        node_a, node_b = MagicMock(), MagicMock()
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (
            _fake_topics(),
            [
                {
                    "source": "Machine Learning",
                    "target": "Data Science",
                    "label": "underpins",
                },
                {
                    "source": "Data Science",
                    "target": "Machine Learning",
                    "label": "feeds into",
                },
            ],
        )
        mock_create_node.side_effect = [node_a, node_b]

        generate_knowledge_map(1)

        self.assertEqual(mock_create_rel.call_count, 2)

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_relationship_skipped_when_source_node_missing(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """A relationship whose source label has no matching node should be skipped."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (
            _fake_topics(),
            [
                {
                    "source": "Nonexistent Topic",
                    "target": "Data Science",
                    "label": "causes",
                }
            ],
        )
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        generate_knowledge_map(1)

        mock_create_rel.assert_not_called()

    @patch("knowledge_app.tasks.NodeRelationship.objects.create")
    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_no_relationships_still_completes_successfully(
        self, mock_get, mock_data, mock_create_node, mock_create_rel
    ):
        """Task should complete successfully even when there are no relationships."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = [MagicMock(), MagicMock()]

        result = generate_knowledge_map(1)

        self.assertEqual(km.status, "complete")
        self.assertIn("successfully", result.lower())
        mock_create_rel.assert_not_called()

    # ------------------------------------------------------------------
    # Failure paths
    # ------------------------------------------------------------------

    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_exception_in_generate_knowledge_map_data_sets_status_to_failed(
        self, mock_get, mock_data
    ):
        """An exception during generate_knowledge_map_data should set status to 'failed'."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.side_effect = RuntimeError("OpenAI API is down")

        generate_knowledge_map(1)

        self.assertEqual(km.status, "failed")

    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_exception_message_returned_as_string(self, mock_get, mock_data):
        """The string form of any unhandled exception should be returned by the task."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.side_effect = RuntimeError("OpenAI API is down")

        result = generate_knowledge_map(1)

        self.assertEqual(result, "OpenAI API is down")

    @patch("knowledge_app.tasks.TopicNode.objects.create")
    @patch("knowledge_app.tasks.generate_knowledge_map_data")
    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_exception_during_db_write_sets_status_to_failed(
        self, mock_get, mock_data, mock_create_node
    ):
        """A database error when creating a TopicNode should mark the map as failed."""
        km = _make_knowledge_map()
        mock_get.return_value = km
        mock_data.return_value = (_fake_topics(), [])
        mock_create_node.side_effect = Exception("DB constraint violation")

        generate_knowledge_map(1)

        self.assertEqual(km.status, "failed")

    # ------------------------------------------------------------------
    # KnowledgeMap.DoesNotExist
    # ------------------------------------------------------------------

    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_knowledge_map_not_found_does_not_raise(self, mock_get):
        """If KnowledgeMap does not exist, the task should return a string not crash."""
        mock_get.side_effect = KnowledgeMap.DoesNotExist(
            "No KnowledgeMap matches id=999"
        )

        try:
            result = generate_knowledge_map(999)
        except UnboundLocalError:
            self.fail(
                "UnboundLocalError raised — knowledge_map was referenced before assignment."
            )

        self.assertIsInstance(result, str)

    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_knowledge_map_not_found_returns_error_string(self, mock_get):
        """When the map doesn't exist, the returned value should be a non-empty string."""
        mock_get.side_effect = KnowledgeMap.DoesNotExist(
            "No KnowledgeMap matches id=999"
        )

        result = generate_knowledge_map(999)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("knowledge_app.tasks.KnowledgeMap.objects.get")
    def test_knowledge_map_not_found_does_not_attempt_save(self, mock_get):
        """When DoesNotExist is raised, no .save() should be attempted on None."""
        mock_get.side_effect = KnowledgeMap.DoesNotExist(
            "No KnowledgeMap matches id=999"
        )

        try:
            generate_knowledge_map(999)
        except AttributeError:
            self.fail("AttributeError raised — task tried to call .save() on None.")
