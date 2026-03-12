from django.test import TestCase, Client
from django.urls import reverse

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