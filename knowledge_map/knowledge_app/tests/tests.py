from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from knowledge_app.models import UploadedFile
from knowledge_app.models import Quiz, Question, QuizAttempt, Answer
import os

#----------------Tests for Authentication---------------------
class AuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_login(self.user)

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

class NavbarTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_login(self.user)

    def test_homepage_link(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)

    def test_maps_link(self):
        response = self.client.get(reverse('maps'))
        self.assertEqual(response.status_code, 200)

    def test_quiz_link(self):
        response = self.client.get(reverse('quizzes'))
        self.assertEqual(response.status_code, 200)

    def test_progress_link(self):
        response = self.client.get(reverse('progress'))
        self.assertEqual(response.status_code, 200)

    def test_sidebar_present_in_page(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, 'id="sidebar"')

    def test_toggle_button_present(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, 'id="toggle-btn"')

    def test_navbar_contains_all_links(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, reverse('homepage'))
        self.assertContains(response, reverse('maps'))
        self.assertContains(response, reverse('quizzes'))
        self.assertContains(response, reverse('progress'))

    def test_navbar_labels(self):
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Maps')
        self.assertContains(response, 'Quiz')
        self.assertContains(response, 'Progress')

    def test_sidebar_present_on_all_pages(self):
        pages = ['homepage', 'maps', 'quizzes', 'progress']
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
        self.client.force_login(self.user)

    def test_upload_page_loads(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)

    def test_upload_page_uses_correct_template(self):
        response = self.client.get(reverse('upload'))
        self.assertTemplateUsed(response, 'knowledge_app/upload.html')

    def test_valid_pdf_upload(self):
        pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        response = self.client.post(reverse('upload'), {'pdf_file': pdf})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.objects.count(), 1)

    def test_non_pdf_upload_rejected(self):
        txt = SimpleUploadedFile("test.txt", b"not a pdf", content_type="text/plain")
        response = self.client.post(reverse('upload'), {'pdf_file': txt})
        self.assertEqual(UploadedFile.objects.count(), 0)

    def test_uploaded_files_appear_in_list(self):
        pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.client.post(reverse('upload'), {'pdf_file': pdf})
        response = self.client.get(reverse('upload'))
        self.assertContains(response, "test.pdf")

    def test_empty_upload_does_nothing(self):
        response = self.client.post(reverse('upload'), {})
        self.assertEqual(UploadedFile.objects.count(), 0)

    def test_model_stores_filename(self):
        pdf = SimpleUploadedFile("myfile.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.client.post(reverse('upload'), {'pdf_file': pdf})
        uploaded = UploadedFile.objects.first()
        self.assertIn("myfile.pdf", uploaded.file.name)

    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)

# ----------------Tests for Delete Feature---------------------

class DeleteFileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.force_login(self.user)

    def test_delete_removes_file_from_database(self):
        pdf = SimpleUploadedFile("delete_me.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        self.client.post(reverse('upload'), {'pdf_file': pdf})
        uploaded = UploadedFile.objects.first()
        self.client.post(reverse('delete_file', args=[uploaded.id]))
        self.assertEqual(UploadedFile.objects.count(), 0)

    def test_delete_nonexistent_file_returns_404(self):
        response = self.client.post(reverse('delete_file', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_selected_files(self):
        pdf1 = SimpleUploadedFile("a.pdf", b"data", content_type="application/pdf")
        pdf2 = SimpleUploadedFile("b.pdf", b"data", content_type="application/pdf")

        self.client.post(reverse('upload'), {'pdf_file': pdf1})
        self.client.post(reverse('upload'), {'pdf_file': pdf2})

        files = UploadedFile.objects.all()

        response = self.client.post(reverse('delete_selected_files'), {
            "selected_files": [f.id for f in files]
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.objects.count(), 0)

    def tearDown(self):
        for f in UploadedFile.objects.all():
            if f.file and os.path.exists(f.file.path):
                os.remove(f.file.path)

# ----------------Tests for Quiz Feature---------------------
class QuizViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    # Test that the quizzes hub page loads successfully for a logged in user
    def test_quiz_url_loads(self):
        response = self.client.get(reverse('quizzes'))
        self.assertEqual(response.status_code, 200)

    # Test that the quizzes hub uses the correct template
    def test_quiz_uses_correct_template(self):
        response = self.client.get(reverse('quizzes'))
        self.assertTemplateUsed(response, 'knowledge_app/quizzes.html')

    # Test that the quiz generation form is present in the page context
    def test_quiz_contains_form(self):
        response = self.client.get(reverse('quizzes'))
        self.assertIn('form', response.context)

    # Test that logged out users are redirected away from the quizzes page
    def test_quiz_redirects_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('quizzes'))
        self.assertEqual(response.status_code, 302)

# ----------------Tests for Quiz Detail View---------------------
class QuizDetailViewTests(TestCase):

    def setUp(self):
        # Create two users, a quiz, and a question before each test
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.quiz = Quiz.objects.create(user=self.owner, title="Test Quiz")
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_text="What is 2+2?",
            question_type="multiple_choice",
            correct_answer="4",
            order=1,
        )
        self.url = reverse("quiz_detail", kwargs={"pk": self.quiz.pk})
        self.client.login(username="owner", password="pass")

    # Test that the quiz detail page loads successfully
    def test_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # Test that the quiz detail page uses the correct template
    def test_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "knowledge_app/quiz_detail.html")

    # Test that submitting answers creates a quiz attempt in the database
    def test_submit_creates_attempt(self):
        self.client.post(self.url, {f"q_{self.question.id}": "4"})
        self.assertEqual(QuizAttempt.objects.filter(quiz=self.quiz).count(), 1)

    # Test that a correct answer results in a score of 100
    def test_correct_answer_scores_100(self):
        self.client.post(self.url, {f"q_{self.question.id}": "4"})
        attempt = QuizAttempt.objects.get(quiz=self.quiz)
        self.assertEqual(attempt.score, 100)
        self.assertEqual(attempt.correct_count, 1)

    # Test that a wrong answer results in a score of 0
    def test_wrong_answer_scores_0(self):
        self.client.post(self.url, {f"q_{self.question.id}": "99"})
        attempt = QuizAttempt.objects.get(quiz=self.quiz)
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.correct_count, 0)

    # Test that submitting a quiz redirects to the results page
    def test_submit_redirects_to_results(self):
        response = self.client.post(self.url, {f"q_{self.question.id}": "4"})
        attempt = QuizAttempt.objects.get(quiz=self.quiz)
        self.assertRedirects(response, reverse("quiz_results", kwargs={"attempt_id": attempt.id}))

    # Test that another user cannot access someone else's quiz
    def test_other_user_gets_404(self):
        self.client.login(username="other", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


# ----------------Tests for Quiz Results View---------------------
class QuizResultsViewTests(TestCase):

    def setUp(self):
        # Create two users, a quiz, a question, an attempt, and an answer before each test
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.quiz = Quiz.objects.create(user=self.owner, title="Test Quiz")
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_text="What is 2+2?",
            question_type="multiple_choice",
            correct_answer="4",
            order=1,
        )
        self.attempt = QuizAttempt.objects.create(
            quiz=self.quiz, user=self.owner,
            score=100, correct_count=1, total_questions=1,
        )
        Answer.objects.create(
            attempt=self.attempt, question=self.question,
            user_answer="4", correct_answer="4", is_correct=True,
        )
        self.url = reverse("quiz_results", kwargs={"attempt_id": self.attempt.pk})
        self.client.login(username="owner", password="pass")

    # Test that the results page loads successfully
    def test_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # Test that the results page uses the correct template
    def test_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "knowledge_app/quiz_results.html")

    # Test that the results page contains the attempt and answers in context
    def test_context_contains_attempt_and_answers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["attempt"], self.attempt)
        self.assertEqual(response.context["answers"].count(), 1)

    # Test that another user cannot view someone else's results
    def test_other_user_gets_404(self):
        self.client.login(username="other", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)




class QuizDetailViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass"
        )

        self.client.login(username="testuser", password="testpass")

        self.quiz = Quiz.objects.create(
            user=self.user,
            title="Test Quiz"
        )

        # Create questions
        self.q1 = Question.objects.create(
            quiz=self.quiz,
            question_text="2+2?",
            correct_answer="4"
        )

        self.q2 = Question.objects.create(
            quiz=self.quiz,
            question_text="Capital of France?",
            correct_answer="Paris"
        )

    # Not logged in
    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('quiz_detail', args=[self.quiz.id]))
        self.assertEqual(response.status_code, 302)

    #  Quiz belongs to another user
    def test_quiz_not_owned_returns_404(self):
        чужой_quiq = Quiz.objects.create(user=self.other_user, title="Other Quiz")
        response = self.client.get(reverse('quiz_detail', args=[чужой_quiq.id]))
        self.assertEqual(response.status_code, 404)

    # GET request renders page
    def test_get_quiz_detail(self):
        response = self.client.get(reverse('quiz_detail', args=[self.quiz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Quiz")

   

    #  Empty answers (edge case)
    def test_submit_quiz_empty_answers(self):
        self.client.post(
            reverse('quiz_detail', args=[self.quiz.id]),
            {}
        )

        attempt = QuizAttempt.objects.first()
        self.assertEqual(attempt.correct_count, 0)
        self.assertEqual(attempt.score, 0)

    #  Quiz with no questions
    def test_quiz_with_no_questions(self):
        empty_quiz = Quiz.objects.create(user=self.user, title="Empty Quiz")

        response = self.client.post(
            reverse('quiz_detail', args=[empty_quiz.id]),
            {}
        )

        attempt = QuizAttempt.objects.first()
        self.assertEqual(attempt.score, 0)

    # Previous attempts appear
    def test_previous_attempts_in_context(self):
        QuizAttempt.objects.create(
            quiz=self.quiz,
            user=self.user,
            score=80,
            correct_count=1,
            total_questions=2
        )

        response = self.client.get(reverse('quiz_detail', args=[self.quiz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("attempts", response.context)

# ----------------Tests for Delete Quiz Feature---------------------
class DeleteQuizTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.quiz = Quiz.objects.create(user=self.user, title='Test Quiz')
        self.url = reverse('delete_quiz', args=[self.quiz.id])

    # Test that deleting a quiz removes it from the database
    def test_delete_quiz_removes_from_database(self):
        self.client.post(self.url)
        self.assertEqual(Quiz.objects.filter(id=self.quiz.id).count(), 0)

    # Test that deleting redirects back to quizzes hub
    def test_delete_quiz_redirects_to_quizzes(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('quizzes'))

    # Test that another user cannot delete someone else's quiz
    def test_other_user_cannot_delete_quiz(self):
        other = User.objects.create_user(username='other', password='pass123')
        c = Client()
        c.login(username='other', password='pass123')
        c.post(self.url)
        self.assertEqual(Quiz.objects.filter(id=self.quiz.id).count(), 1)

    # Test that deleting a nonexistent quiz does not crash
    def test_delete_nonexistent_quiz_does_not_crash(self):
        response = self.client.post(reverse('delete_quiz', args=[99999]))
        self.assertRedirects(response, reverse('quizzes'))

    # Test that GET request does not delete the quiz
    def test_get_request_does_not_delete_quiz(self):
        self.client.get(self.url)
        self.assertEqual(Quiz.objects.filter(id=self.quiz.id).count(), 1)