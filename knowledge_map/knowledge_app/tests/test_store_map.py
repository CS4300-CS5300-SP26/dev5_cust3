from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from knowledge_app.models import UploadedFile, KnowledgeMap
import os


class StoreMapTest(TestCase):
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

    # Test maps page loads correctly
    def test_maps_page_loads(self):
        response = self.client.get(reverse('maps'))
        self.assertEqual(response.status_code, 200)

    # Test maps page uses correct template
    def test_maps_page_uses_correct_template(self):
        response = self.client.get(reverse('maps'))
        self.assertTemplateUsed(response, 'knowledge_app/maps.html')

    # Test maps page shows user's maps
    def test_maps_page_shows_user_maps(self):
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'Test Map')

    # Test maps page does not show other user's maps
    def test_maps_page_does_not_show_other_users_maps(self):
        KnowledgeMap.objects.create(
            user=self.other_user,
            uploaded_file=self.uploaded_file,
            title='Other User Map',
            status='complete'
        )
        response = self.client.get(reverse('maps'))
        self.assertNotContains(response, 'Other User Map')

    # Test maps page shows correct status
    def test_maps_page_shows_correct_status(self):
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'complete')

    # Test maps page shows view map button for complete maps
    def test_maps_page_shows_view_button_for_complete_maps(self):
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'View Map')

    # Test maps page shows pending message for incomplete maps
    def test_maps_page_shows_pending_for_incomplete_maps(self):
        KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Pending Map',
            status='pending'
        )
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'Pending...')

    # Test maps page shows empty state when no maps
    def test_maps_page_shows_empty_state(self):
        KnowledgeMap.objects.all().delete()
        response = self.client.get(reverse('maps'))
        self.assertContains(response, "You haven't created any maps yet.")

    # Test maps are ordered newest first
    # Test maps are ordered newest first
    def test_maps_ordered_newest_first(self):
        newer_map = KnowledgeMap.objects.create(
            user=self.user,
            uploaded_file=self.uploaded_file,
            title='Newer Map',
            status='complete'
        )
        response = self.client.get(reverse('maps'))
        maps = list(response.context['maps'])
        self.assertEqual(maps[0].id, newer_map.id)
        self.assertEqual(maps[1].id, self.knowledge_map.id)

    # Test unauthenticated user is redirected
    def test_unauthenticated_user_redirected(self):
        self.client.logout()
        response = self.client.get(reverse('maps'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    # Test maps page shows create new map button
    def test_maps_page_shows_create_map_button(self):
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'Create New Map')

    # Clean up uploaded test files after tests run
    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)