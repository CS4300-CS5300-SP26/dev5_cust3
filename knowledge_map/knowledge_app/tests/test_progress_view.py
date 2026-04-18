from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from knowledge_app.models import Quiz, Question, QuizAttempt, Answer

# ----------------Tests for Progress/Mastery Feature---------------------


class ProgressViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create a quiz with one question for reuse across tests
        self.quiz = Quiz.objects.create(
            user=self.user,
            title='Test Quiz',
            difficulty='medium'
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_text='What is 2+2?',
            question_type='multiple_choice',
            correct_answer='4',
            order=1
        )

    # Test that the progress page loads successfully
    def test_page_loads(self):
        response = self.client.get(reverse('progress'))
        self.assertEqual(response.status_code, 200)

    # Test that the progress page uses the correct template
    def test_correct_template(self):
        response = self.client.get(reverse('progress'))
        self.assertTemplateUsed(response, 'knowledge_app/progress.html')

    # Test that logged out users are redirected away from the progress page
    def test_redirects_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('progress'))
        self.assertEqual(response.status_code, 302)

    # Test that a quiz with no attempts shows as not_attempted
    def test_no_attempts_shows_not_attempted(self):
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        self.assertEqual(quiz_data[0]['status'], 'not_attempted')

    # Test that a score of 80+ is marked as mastered
    def test_score_80_or_above_is_mastered(self):
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=85, correct_count=1, total_questions=1
        )
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        self.assertEqual(quiz_data[0]['status'], 'mastered')

    # Test that a score between 60-79 is marked as learning
    def test_score_60_to_79_is_learning(self):
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=70, correct_count=1, total_questions=1
        )
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        self.assertEqual(quiz_data[0]['status'], 'learning')

    # Test that a score below 60 is marked as needs_practice
    def test_score_below_60_is_needs_practice(self):
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=45, correct_count=1, total_questions=1
        )
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        self.assertEqual(quiz_data[0]['status'], 'needs_practice')

    # Test that the context contains the correct summary counts
    def test_context_contains_summary_counts(self):
        response = self.client.get(reverse('progress'))
        self.assertIn('total', response.context)
        self.assertIn('mastered', response.context)
        self.assertIn('learning', response.context)
        self.assertIn('needs_practice', response.context)
        self.assertIn('not_attempted', response.context)

    # Test that only the logged in user's quizzes appear
    def test_only_shows_current_users_quizzes(self):
        other = User.objects.create_user(
            username='other', password='pass123')
        Quiz.objects.create(user=other, title='Other Quiz')
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        for item in quiz_data:
            self.assertEqual(item['quiz'].user, self.user)

    # Test that highest score is tracked correctly across multiple attempts
    def test_highest_score_tracked(self):
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=50, correct_count=1, total_questions=1
        )
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=90, correct_count=1, total_questions=1
        )
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        self.assertEqual(quiz_data[0]['highest_score'], 90)

    # Test that status is based on latest attempt not highest
    def test_status_based_on_latest_not_highest(self):
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=90, correct_count=1, total_questions=1
        )
        QuizAttempt.objects.create(
            quiz=self.quiz, user=self.user,
            score=40, correct_count=1, total_questions=1
        )
        response = self.client.get(reverse('progress'))
        quiz_data = response.context['quiz_data']
        # Latest was 40 so should be needs_practice even though highest was 90
        self.assertEqual(quiz_data[0]['status'], 'needs_practice')