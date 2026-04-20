from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from knowledge_app.models import UploadedFile, KnowledgeMap, SharedMap
import os
import json


class ShareMapTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Create owner and another user
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.unrelated_user = User.objects.create_user(username='unrelated', password='testpass123')

        self.client.login(username='owner', password='testpass123')

        # Create uploaded file and knowledge map
        self.uploaded_file = UploadedFile.objects.create(
            file=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        )
        self.knowledge_map = KnowledgeMap.objects.create(
            user=self.owner,
            uploaded_file=self.uploaded_file,
            title='Test Map',
            status='complete'
        )

    # -------------------------------------------------------------------------
    # GET share_map page
    # -------------------------------------------------------------------------

    def test_share_page_loads(self):
        """Share page should load for the map owner."""
        response = self.client.get(reverse('share_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 200)

    def test_share_page_uses_correct_template(self):
        """Share page should use the share_map template."""
        response = self.client.get(reverse('share_map', args=[self.knowledge_map.id]))
        self.assertTemplateUsed(response, 'knowledge_app/share_map.html')

    def test_share_page_requires_login(self):
        """Unauthenticated users should be redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('share_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_share_page_returns_404_for_other_users_map(self):
        """Non-owner should get 404 when trying to access share page."""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('share_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.status_code, 404)

    def test_share_page_context_contains_knowledge_map(self):
        """Share page context should contain the knowledge map."""
        response = self.client.get(reverse('share_map', args=[self.knowledge_map.id]))
        self.assertEqual(response.context['knowledge_map'], self.knowledge_map)

    # -------------------------------------------------------------------------
    # Public link sharing
    # -------------------------------------------------------------------------

    def test_generate_public_link_creates_shared_map(self):
        """POST with share_type=public should create a SharedMap record."""
        self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'public'
        })
        self.assertEqual(SharedMap.objects.filter(
            knowledge_map=self.knowledge_map, is_public=True
        ).count(), 1)

    def test_generate_public_link_returns_share_url(self):
        """POST with share_type=public should return a share_url in JSON."""
        response = self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'public'
        })
        data = json.loads(response.content)
        self.assertIn('share_url', data)

    def test_generate_public_link_twice_does_not_create_duplicate(self):
        """Generating a public link twice should not create duplicate records."""
        self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {'share_type': 'public'})
        self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {'share_type': 'public'})
        self.assertEqual(SharedMap.objects.filter(
            knowledge_map=self.knowledge_map, is_public=True
        ).count(), 1)

    def test_public_link_is_accessible_without_login(self):
        """Anyone with the public link should be able to view the map."""
        SharedMap.objects.create(
            knowledge_map=self.knowledge_map,
            is_public=True
        )
        shared = SharedMap.objects.get(knowledge_map=self.knowledge_map, is_public=True)
        self.client.logout()
        response = self.client.get(reverse('view_shared_map', args=[shared.share_token]))
        self.assertEqual(response.status_code, 200)

    def test_public_shared_map_uses_correct_template(self):
        """Public shared map should use the view_shared_map template."""
        SharedMap.objects.create(knowledge_map=self.knowledge_map, is_public=True)
        shared = SharedMap.objects.get(knowledge_map=self.knowledge_map, is_public=True)
        self.client.logout()
        response = self.client.get(reverse('view_shared_map', args=[shared.share_token]))
        self.assertTemplateUsed(response, 'knowledge_app/view_shared_map.html')

    # -------------------------------------------------------------------------
    # Share with specific user
    # -------------------------------------------------------------------------

    def test_share_with_user_creates_shared_map(self):
        """POST with share_type=user should create a SharedMap for that user."""
        self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'user',
            'username': 'otheruser'
        })
        self.assertTrue(SharedMap.objects.filter(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user
        ).exists())

    def test_share_with_user_returns_success_message(self):
        """POST with share_type=user should return a success message in JSON."""
        response = self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'user',
            'username': 'otheruser'
        })
        data = json.loads(response.content)
        self.assertIn('message', data)

    def test_share_with_nonexistent_user_returns_404(self):
        """Sharing with a username that doesn't exist should return 404."""
        response = self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'user',
            'username': 'doesnotexist'
        })
        self.assertEqual(response.status_code, 404)

    def test_share_with_yourself_returns_400(self):
        """Sharing with yourself should return 400."""
        response = self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'user',
            'username': 'owner'
        })
        self.assertEqual(response.status_code, 400)

    def test_share_with_user_twice_does_not_create_duplicate(self):
        """Sharing with the same user twice should not create duplicate records."""
        self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'user', 'username': 'otheruser'
        })
        self.client.post(reverse('share_map', args=[self.knowledge_map.id]), {
            'share_type': 'user', 'username': 'otheruser'
        })
        self.assertEqual(SharedMap.objects.filter(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user
        ).count(), 1)

    # -------------------------------------------------------------------------
    # View shared map access control
    # -------------------------------------------------------------------------

    def test_user_shared_map_accessible_to_shared_user(self):
        """A user-specific shared map should be accessible to the shared user."""
        shared = SharedMap.objects.create(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user,
            is_public=False
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('view_shared_map', args=[shared.share_token]))
        self.assertEqual(response.status_code, 200)

    def test_user_shared_map_not_accessible_to_unrelated_user(self):
        """A user-specific shared map should not be accessible to other users."""
        shared = SharedMap.objects.create(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user,
            is_public=False
        )
        self.client.login(username='unrelated', password='testpass123')
        response = self.client.get(reverse('view_shared_map', args=[shared.share_token]))
        self.assertEqual(response.status_code, 403)

    def test_user_shared_map_redirects_unauthenticated_user(self):
        """A user-specific shared map should redirect unauthenticated users to login."""
        shared = SharedMap.objects.create(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user,
            is_public=False
        )
        self.client.logout()
        response = self.client.get(reverse('view_shared_map', args=[shared.share_token]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_invalid_share_token_returns_404(self):
        """An invalid share token should return 404."""
        import uuid
        response = self.client.get(reverse('view_shared_map', args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

    
    # -------------------------------------------------------------------------
    # Maps page shared with me section
    # -------------------------------------------------------------------------

    def test_maps_page_shows_shared_maps(self):
        """Maps page should show maps shared with the logged in user."""
        SharedMap.objects.create(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user,
            is_public=False
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'Shared with Me')
        self.assertContains(response, 'Test Map')

    def test_maps_page_does_not_show_shared_maps_to_wrong_user(self):
        """Maps page should not show shared maps to users they were not shared with."""
        SharedMap.objects.create(
            knowledge_map=self.knowledge_map,
            shared_with=self.other_user,
            is_public=False
        )
        self.client.login(username='unrelated', password='testpass123')
        response = self.client.get(reverse('maps'))
        self.assertNotContains(response, 'Shared with Me')

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)