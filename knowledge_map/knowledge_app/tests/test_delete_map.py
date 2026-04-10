from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from knowledge_app.models import UploadedFile, KnowledgeMap
import os

# ----------------Tests for Delete Map Feature---------------------
class DeleteMapTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create a test uploaded file
        self.uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        )

        # Create a test knowledge map
        self.knowledge_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Test Map',
            status='complete'
        )

    # Test deleting a map removes it from the database
    def test_delete_map_removes_from_database(self):
        self.client.post(reverse('delete_map', args=[self.knowledge_map.id]))
        self.assertEqual(KnowledgeMap.objects.count(), 0)

    # Test deleting a map redirects to maps page
    def test_delete_map_redirects_to_maps(self):
        response = self.client.post(reverse('delete_map', args=[self.knowledge_map.id]))
        self.assertRedirects(response, reverse('maps'))

    # Test deleting a map that doesn't exist returns 404
    def test_delete_nonexistent_map_returns_404(self):
        response = self.client.post(reverse('delete_map', args=[999]))
        self.assertEqual(response.status_code, 404)

    # Test a user cannot delete another user's map
    def test_cannot_delete_another_users_map(self):
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(reverse('delete_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(KnowledgeMap.objects.count(), 1)

    # Test GET request does not delete the map
    def test_get_request_does_not_delete_map(self):
        self.client.get(reverse('delete_map', args=[self.knowledge_map.id]))
        self.assertEqual(KnowledgeMap.objects.count(), 1)

    # Test unauthenticated user cannot delete a map
    def test_unauthenticated_user_cannot_delete_map(self):
        self.client.logout()
        self.client.post(reverse('delete_map', args=[self.knowledge_map.id]))
        self.assertEqual(KnowledgeMap.objects.count(), 1)

    # Clean up uploaded test files after tests run
    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)