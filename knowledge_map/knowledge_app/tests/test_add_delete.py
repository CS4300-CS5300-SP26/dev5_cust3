import json
import os

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from knowledge_app.models import (KnowledgeMap, NodeRelationship, TopicNode,
                                  UploadedFile)


class AddDeleteNodeTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile(
                "test.pdf", b"%PDF-1.4 test", content_type="application/pdf"
            )
        )
        self.knowledge_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title="Test Map",
            status="complete",
        )

    # -------------------------------------------------------------------------
    # Add node
    # -------------------------------------------------------------------------

    def test_add_node_creates_topic_node(self):
        """POST to add_node should create a TopicNode in the database."""
        self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "New Topic", "summary": "A summary"}),
            content_type="application/json",
        )
        self.assertEqual(
            TopicNode.objects.filter(knowledge_map=self.knowledge_map).count(), 1
        )

    def test_add_node_returns_node_data(self):
        """POST to add_node should return the new node's id, label and summary."""
        response = self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "New Topic", "summary": "A summary"}),
            content_type="application/json",
        )
        data = json.loads(response.content)
        self.assertIn("id", data)
        self.assertEqual(data["label"], "New Topic")
        self.assertEqual(data["summary"], "A summary")

    def test_add_node_without_label_returns_400(self):
        """POST to add_node without a label should return 400."""
        response = self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "", "summary": "A summary"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_add_node_without_label_does_not_create_node(self):
        """POST to add_node without a label should not create a TopicNode."""
        self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "", "summary": "A summary"}),
            content_type="application/json",
        )
        self.assertEqual(TopicNode.objects.count(), 0)

    def test_add_node_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "New Topic", "summary": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_add_node_to_other_users_map_returns_404(self):
        """Adding a node to another user's map should return 404."""
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "New Topic", "summary": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_add_node_get_request_returns_405(self):
        """GET request to add_node should return 405."""
        response = self.client.get(reverse("add_node", args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 405)

    def test_add_node_without_summary_succeeds(self):
        """Adding a node without a summary should still work."""
        response = self.client.post(
            reverse("add_node", args=[self.knowledge_map.id]),
            data=json.dumps({"label": "New Topic"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TopicNode.objects.count(), 1)

    # -------------------------------------------------------------------------
    # Delete node
    # -------------------------------------------------------------------------

    def test_delete_node_removes_from_database(self):
        """POST to delete_node should remove the TopicNode from the database."""
        node = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic to delete", summary="Summary"
        )
        self.client.post(reverse("delete_node", args=[self.knowledge_map.id, node.id]))
        self.assertFalse(TopicNode.objects.filter(id=node.id).exists())

    def test_delete_node_returns_success(self):
        """POST to delete_node should return success JSON."""
        node = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic to delete", summary="Summary"
        )
        response = self.client.post(
            reverse("delete_node", args=[self.knowledge_map.id, node.id])
        )
        data = json.loads(response.content)
        self.assertTrue(data["success"])

    def test_delete_nonexistent_node_returns_404(self):
        """Deleting a node that doesn't exist should return 404."""
        response = self.client.post(
            reverse("delete_node", args=[self.knowledge_map.id, 9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_node_from_other_users_map_returns_404(self):
        """Deleting a node from another user's map should return 404."""
        node = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic", summary="Summary"
        )
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(
            reverse("delete_node", args=[self.knowledge_map.id, node.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_node_requires_login(self):
        """Unauthenticated users should be redirected."""
        node = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic", summary="Summary"
        )
        self.client.logout()
        response = self.client.post(
            reverse("delete_node", args=[self.knowledge_map.id, node.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_node_get_request_returns_405(self):
        """GET request to delete_node should return 405."""
        node = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic", summary="Summary"
        )
        response = self.client.get(
            reverse("delete_node", args=[self.knowledge_map.id, node.id])
        )
        self.assertEqual(response.status_code, 405)


class AddDeleteRelationshipTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile(
                "test.pdf", b"%PDF-1.4 test", content_type="application/pdf"
            )
        )
        self.knowledge_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title="Test Map",
            status="complete",
        )
        self.node_a = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic A", summary="Summary A"
        )
        self.node_b = TopicNode.objects.create(
            knowledge_map=self.knowledge_map, label="Topic B", summary="Summary B"
        )

    # -------------------------------------------------------------------------
    # Add relationship
    # -------------------------------------------------------------------------

    def test_add_relationship_creates_node_relationship(self):
        """POST to add_relationship should create a NodeRelationship in the database."""
        self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {
                    "source_id": self.node_a.id,
                    "target_id": self.node_b.id,
                    "label": "leads to",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(
            NodeRelationship.objects.filter(knowledge_map=self.knowledge_map).count(), 1
        )

    def test_add_relationship_returns_edge_data(self):
        """POST to add_relationship should return edge id, source, target and label."""
        response = self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {
                    "source_id": self.node_a.id,
                    "target_id": self.node_b.id,
                    "label": "leads to",
                }
            ),
            content_type="application/json",
        )
        data = json.loads(response.content)
        self.assertIn("id", data)
        self.assertEqual(data["source"], str(self.node_a.id))
        self.assertEqual(data["target"], str(self.node_b.id))
        self.assertEqual(data["label"], "leads to")

    def test_add_relationship_without_label_returns_400(self):
        """POST to add_relationship without a label should return 400."""
        response = self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {"source_id": self.node_a.id, "target_id": self.node_b.id, "label": ""}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_add_relationship_without_source_returns_400(self):
        """POST to add_relationship without source_id should return 400."""
        response = self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps({"target_id": self.node_b.id, "label": "leads to"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_add_duplicate_relationship_returns_400(self):
        """Adding the same relationship twice should return 400."""
        self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {
                    "source_id": self.node_a.id,
                    "target_id": self.node_b.id,
                    "label": "leads to",
                }
            ),
            content_type="application/json",
        )
        response = self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {
                    "source_id": self.node_a.id,
                    "target_id": self.node_b.id,
                    "label": "leads to",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(NodeRelationship.objects.count(), 1)

    def test_add_relationship_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {
                    "source_id": self.node_a.id,
                    "target_id": self.node_b.id,
                    "label": "leads to",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_add_relationship_to_other_users_map_returns_404(self):
        """Adding a relationship to another user's map should return 404."""
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(
            reverse("add_relationship", args=[self.knowledge_map.id]),
            data=json.dumps(
                {
                    "source_id": self.node_a.id,
                    "target_id": self.node_b.id,
                    "label": "leads to",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_add_relationship_get_request_returns_405(self):
        """GET request to add_relationship should return 405."""
        response = self.client.get(
            reverse("add_relationship", args=[self.knowledge_map.id])
        )
        self.assertEqual(response.status_code, 405)

    # -------------------------------------------------------------------------
    # Delete relationship
    # -------------------------------------------------------------------------

    def test_delete_relationship_removes_from_database(self):
        """POST to delete_relationship should remove the NodeRelationship."""
        relationship = NodeRelationship.objects.create(
            knowledge_map=self.knowledge_map,
            source_topic=self.node_a,
            target_topic=self.node_b,
            relationship_label="leads to",
        )
        self.client.post(
            reverse(
                "delete_relationship", args=[self.knowledge_map.id, relationship.id]
            )
        )
        self.assertFalse(NodeRelationship.objects.filter(id=relationship.id).exists())

    def test_delete_relationship_returns_success(self):
        """POST to delete_relationship should return success JSON."""
        relationship = NodeRelationship.objects.create(
            knowledge_map=self.knowledge_map,
            source_topic=self.node_a,
            target_topic=self.node_b,
            relationship_label="leads to",
        )
        response = self.client.post(
            reverse(
                "delete_relationship", args=[self.knowledge_map.id, relationship.id]
            )
        )
        data = json.loads(response.content)
        self.assertTrue(data["success"])

    def test_delete_nonexistent_relationship_returns_404(self):
        """Deleting a relationship that doesn't exist should return 404."""
        response = self.client.post(
            reverse("delete_relationship", args=[self.knowledge_map.id, 9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_relationship_from_other_users_map_returns_404(self):
        """Deleting a relationship from another user's map should return 404."""
        relationship = NodeRelationship.objects.create(
            knowledge_map=self.knowledge_map,
            source_topic=self.node_a,
            target_topic=self.node_b,
            relationship_label="leads to",
        )
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(
            reverse(
                "delete_relationship", args=[self.knowledge_map.id, relationship.id]
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_relationship_requires_login(self):
        """Unauthenticated users should be redirected."""
        relationship = NodeRelationship.objects.create(
            knowledge_map=self.knowledge_map,
            source_topic=self.node_a,
            target_topic=self.node_b,
            relationship_label="leads to",
        )
        self.client.logout()
        response = self.client.post(
            reverse(
                "delete_relationship", args=[self.knowledge_map.id, relationship.id]
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_relationship_get_request_returns_405(self):
        """GET request to delete_relationship should return 405."""
        relationship = NodeRelationship.objects.create(
            knowledge_map=self.knowledge_map,
            source_topic=self.node_a,
            target_topic=self.node_b,
            relationship_label="leads to",
        )
        response = self.client.get(
            reverse(
                "delete_relationship", args=[self.knowledge_map.id, relationship.id]
            )
        )
        self.assertEqual(response.status_code, 405)

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)
