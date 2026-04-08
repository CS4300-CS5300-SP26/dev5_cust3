import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from knowledge_app.models import UploadedFile, KnowledgeMap, TopicNode, NodeRelationship
from django.core.files.uploadedfile import SimpleUploadedFile
import os


class ViewMapViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create a fake uploaded file
        pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.uploaded_file = UploadedFile.objects.create(
            file=pdf,
            user=self.user
        )

        # Create a knowledge map for the user
        self.knowledge_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Test Map',
            status='complete'
        )

        # Create two topic nodes
        self.node_a = TopicNode.objects.create(
            knowledge_map=self.knowledge_map,
            label='Machine Learning',
            summary='Covers ML algorithms.'
        )
        self.node_b = TopicNode.objects.create(
            knowledge_map=self.knowledge_map,
            label='Data Science',
            summary='Covers data analysis.'
        )

        # Create a relationship between the nodes
        self.relationship = NodeRelationship.objects.create(
            knowledge_map=self.knowledge_map,
            source_topic=self.node_a,
            target_topic=self.node_b,
            relationship_label='underpins'
        )

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    def test_redirects_to_login_if_not_logged_in(self):
        """Unauthenticated users should be redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('view_map', args=[self.knowledge_map.id])}"
        )

    def test_returns_404_for_another_users_map(self):
        """A user should not be able to view another user's map."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_nonexistent_map(self):
        """Requesting a map that doesn't exist should return 404."""
        response = self.client.get(reverse('view_map', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------------------
    # GET requests
    # -------------------------------------------------------------------------

    def test_get_returns_200(self):
        """A valid GET request should return 200."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 200)

    def test_get_uses_correct_template(self):
        """The view should render the view_map template."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertTemplateUsed(response, 'knowledge_app/view_map.html')

    # -------------------------------------------------------------------------
    # Context - knowledge_map
    # -------------------------------------------------------------------------

    def test_context_contains_knowledge_map(self):
        """The context should include the knowledge_map object."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertIn('knowledge_map', response.context)

    def test_context_knowledge_map_is_correct(self):
        """The knowledge_map in context should match the requested map."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.context['knowledge_map'], self.knowledge_map)

    # -------------------------------------------------------------------------
    # Context - nodes
    # -------------------------------------------------------------------------

    def test_context_contains_nodes(self):
        """The context should include a nodes list."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertIn('nodes', response.context)

    def test_nodes_count_matches_topics(self):
        """The number of nodes should match the number of topic nodes."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertEqual(len(response.context['nodes']), 2)

    def test_nodes_have_correct_structure(self):
        """Each node should have a 'data' key with 'id', 'label', and 'summary'."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        for node in response.context['nodes']:
            self.assertIn('data', node)
            self.assertIn('id', node['data'])
            self.assertIn('label', node['data'])
            self.assertIn('summary', node['data'])

    def test_node_label_matches_topic(self):
        """Node labels should match the topic node labels."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        node_labels = [n['data']['label'] for n in response.context['nodes']]
        self.assertIn('Machine Learning', node_labels)
        self.assertIn('Data Science', node_labels)

    def test_node_id_is_string(self):
        """Node ids should be strings for Cytoscape.js compatibility."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        for node in response.context['nodes']:
            self.assertIsInstance(node['data']['id'], str)

    def test_node_summary_matches_topic(self):
        """Node summaries should match the topic node summaries."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        node_summaries = [n['data']['summary'] for n in response.context['nodes']]
        self.assertIn('Covers ML algorithms.', node_summaries)

    # -------------------------------------------------------------------------
    # Context - edges
    # -------------------------------------------------------------------------

    def test_context_contains_edges(self):
        """The context should include an edges list."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertIn('edges', response.context)

    def test_edges_count_matches_relationships(self):
        """The number of edges should match the number of relationships."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        self.assertEqual(len(response.context['edges']), 1)

    def test_edges_have_correct_structure(self):
        """Each edge should have a 'data' key with 'id', 'source', 'target', and 'label'."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        for edge in response.context['edges']:
            self.assertIn('data', edge)
            self.assertIn('id', edge['data'])
            self.assertIn('source', edge['data'])
            self.assertIn('target', edge['data'])
            self.assertIn('label', edge['data'])

    def test_edge_id_prefixed_with_e(self):
        """Edge ids should be prefixed with 'e' for Cytoscape.js."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        for edge in response.context['edges']:
            self.assertTrue(edge['data']['id'].startswith('e'))

    def test_edge_source_and_target_are_strings(self):
        """Edge source and target should be strings for Cytoscape.js compatibility."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        for edge in response.context['edges']:
            self.assertIsInstance(edge['data']['source'], str)
            self.assertIsInstance(edge['data']['target'], str)

    def test_edge_label_matches_relationship(self):
        """Edge label should match the relationship label."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        edge_labels = [e['data']['label'] for e in response.context['edges']]
        self.assertIn('underpins', edge_labels)

    def test_edge_source_matches_source_topic(self):
        """Edge source id should match the source topic node id."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        edge = response.context['edges'][0]
        self.assertEqual(edge['data']['source'], str(self.node_a.id))

    def test_edge_target_matches_target_topic(self):
        """Edge target id should match the target topic node id."""
        response = self.client.get(reverse('view_map', args=[self.knowledge_map.id]))
        edge = response.context['edges'][0]
        self.assertEqual(edge['data']['target'], str(self.node_b.id))

    # -------------------------------------------------------------------------
    # Empty map (no topics or relationships)
    # -------------------------------------------------------------------------

    def test_empty_map_returns_empty_nodes(self):
        """A map with no topics should return an empty nodes list."""
        empty_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Empty Map',
            status='complete'
        )
        response = self.client.get(reverse('view_map', args=[empty_map.id]))
        self.assertEqual(response.context['nodes'], [])

    def test_empty_map_returns_empty_edges(self):
        """A map with no relationships should return an empty edges list."""
        empty_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Empty Map',
            status='complete'
        )
        response = self.client.get(reverse('view_map', args=[empty_map.id]))
        self.assertEqual(response.context['edges'], [])

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)


# =============================================================================
# Tests for map_status API endpoint
# =============================================================================

class MapStatusViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.uploaded_file = UploadedFile.objects.create(
            file=pdf,
            user=self.user
        )
        self.knowledge_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Test Map',
            status='pending'
        )

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    def test_redirects_to_login_if_not_logged_in(self):
        """Unauthenticated users should be redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 302)

    def test_returns_404_for_another_users_map(self):
        """A user should not be able to check status of another user's map."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_nonexistent_map(self):
        """Requesting status of a map that doesn't exist should return 404."""
        response = self.client.get(reverse('map_status', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------------------
    # Response format
    # -------------------------------------------------------------------------

    def test_returns_200(self):
        """A valid request should return 200."""
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 200)

    def test_returns_json(self):
        """The response should be JSON."""
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_response_contains_status_key(self):
        """The JSON response should contain a 'status' key."""
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        data = json.loads(response.content)
        self.assertIn('status', data)

    # -------------------------------------------------------------------------
    # Status values
    # -------------------------------------------------------------------------

    def test_returns_pending_status(self):
        """Should return 'pending' when map status is pending."""
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'pending')

    def test_returns_complete_status(self):
        """Should return 'complete' when map status is complete."""
        self.knowledge_map.status = 'complete'
        self.knowledge_map.save()
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'complete')

    def test_returns_failed_status(self):
        """Should return 'failed' when map status is failed."""
        self.knowledge_map.status = 'failed'
        self.knowledge_map.save()
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'failed')

    def test_returns_processing_status(self):
        """Should return 'processing' when map status is processing."""
        self.knowledge_map.status = 'processing'
        self.knowledge_map.save()
        response = self.client.get(reverse('map_status', args=[self.knowledge_map.id]))
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'processing')

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)