from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UploadedFile
import os

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

# ----------------Tests for Quiz Feature---------------------
class QuizViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_quiz_url_loads(self):
        response = self.client.get(reverse('quiz'))
        self.assertEqual(response.status_code, 200)

    def test_quiz_uses_correct_template(self):
        response = self.client.get(reverse('quiz'))
        self.assertTemplateUsed(response, 'knowledge_app/quiz.html')

    def test_quiz_contains_questions(self):
        response = self.client.get(reverse('quiz'))
        self.assertIn('quiz', response.context)
        self.assertGreater(len(response.context['quiz']), 0)

    def test_quiz_post_returns_score(self):
        response = self.client.post(reverse('quiz'), {})
        self.assertIn('score', response.context)