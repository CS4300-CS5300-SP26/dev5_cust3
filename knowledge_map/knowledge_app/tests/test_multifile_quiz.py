from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from knowledge_app.forms import QuizGenerationForm
from knowledge_app.models import Question, Quiz, UploadedFile
from knowledge_app.views import check_answer

# ----------------Tests for Multi-File Quiz Generation---------------------


class MultiFileQuizFormTest(TestCase):
    """Tests for QuizGenerationForm with multiple file selection"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser_form", password="testpass123"
        )
        # Create two uploaded files with extracted text
        self.file1 = UploadedFile.objects.create(
            user=self.user,
            file=SimpleUploadedFile("crabs.pdf", b"fake pdf content"),
            original_filename="crabs.pdf",
            extracted_text="Crabs are crustaceans with ten legs and a hard exoskeleton.",
        )
        self.file2 = UploadedFile.objects.create(
            user=self.user,
            file=SimpleUploadedFile("animals.pdf", b"fake pdf content"),
            original_filename="animals.pdf",
            extracted_text="A cow makes a mooing sound. A dog makes a barking sound.",
        )

    def test_form_accepts_multiple_files(self):
        """Form should be valid when multiple existing files are selected"""
        form = QuizGenerationForm(
            data={
                "title": "Multi-file Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [self.file1.pk, self.file2.pk],
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_accepts_single_file(self):
        """Form should still be valid with just one file selected"""
        form = QuizGenerationForm(
            data={
                "title": "Single File Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [self.file1.pk],
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_with_no_files_selected(self):
        """Form should be invalid when existing is chosen but no files selected"""
        form = QuizGenerationForm(
            data={
                "title": "Empty Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [],
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())

    def test_form_only_shows_user_files(self):
        """Form queryset should only include files belonging to the user"""
        other_user = User.objects.create_user(
            username="other_user", password="testpass123"
        )
        other_file = UploadedFile.objects.create(
            user=other_user,
            file=SimpleUploadedFile("other.pdf", b"fake pdf content"),
            original_filename="other.pdf",
        )
        form = QuizGenerationForm(user=self.user)
        queryset = form.fields["existing_pdf"].queryset
        self.assertIn(self.file1, queryset)
        self.assertIn(self.file2, queryset)
        self.assertNotIn(other_file, queryset)


# ----------------Tests for Multi-File Text Extraction in View---------------------


class MultiFileQuizViewTest(TestCase):
    """Tests for quizzes_hub view with multiple file selection"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser_view", password="testpass123"
        )
        self.client.login(username="testuser_view", password="testpass123")

        self.file1 = UploadedFile.objects.create(
            user=self.user,
            file=SimpleUploadedFile("crabs.pdf", b"fake pdf content"),
            original_filename="crabs.pdf",
            extracted_text="Crabs are crustaceans with ten legs and a hard exoskeleton.",
        )
        self.file2 = UploadedFile.objects.create(
            user=self.user,
            file=SimpleUploadedFile("animals.pdf", b"fake pdf content"),
            original_filename="animals.pdf",
            extracted_text="A cow makes a mooing sound. A dog makes a barking sound.",
        )

    def _fake_generate(self, captured_text):
        """Returns a side_effect function that saves text and creates a question"""
        def fake(quiz, text, **kwargs):
            captured_text.append(text)
            Question.objects.create(
                quiz=quiz,
                question_text="Test question?",
                question_type="multiple_choice",
                choices=["a", "b", "c", "d"],
                correct_answer="a",
                order=1,
            )
        return fake

    @patch("knowledge_app.views.generate_quiz_from_text")
    def test_multifile_concatenates_text(self, mock_generate):
        """Both files extracted_text should be concatenated and passed to generator"""
        captured = []
        mock_generate.side_effect = self._fake_generate(captured)
        self.client.post(
            reverse("quizzes"),
            {
                "title": "Multi-file Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [self.file1.pk, self.file2.pk],
            },
        )
        self.assertTrue(len(captured) > 0)
        self.assertIn("Crabs are crustaceans", captured[0])
        self.assertIn("cow makes a mooing sound", captured[0])

    @patch("knowledge_app.views.generate_quiz_from_text")
    def test_multifile_sets_source_file_to_first(self, mock_generate):
        """source_file on the quiz should be set to the first selected file"""
        captured = []
        mock_generate.side_effect = self._fake_generate(captured)
        self.client.post(
            reverse("quizzes"),
            {
                "title": "Multi-file Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [self.file1.pk, self.file2.pk],
            },
        )
        quiz = Quiz.objects.filter(user=self.user).latest("id")
        self.assertIsNotNone(quiz.source_file)

    @patch("knowledge_app.views.generate_quiz_from_text")
    def test_single_file_still_works(self, mock_generate):
        """Single file selection should still work correctly"""
        captured = []
        mock_generate.side_effect = self._fake_generate(captured)
        self.client.post(
            reverse("quizzes"),
            {
                "title": "Single File Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [self.file1.pk],
            },
        )
        self.assertTrue(len(captured) > 0)
        self.assertIn("Crabs are crustaceans", captured[0])

    @patch("knowledge_app.views.generate_quiz_from_text")
    def test_empty_extracted_text_still_creates_quiz(self, mock_generate):
        """Quiz should still be created even if a file has no extracted text"""
        captured = []
        mock_generate.side_effect = self._fake_generate(captured)
        empty_file = UploadedFile.objects.create(
            user=self.user,
            file=SimpleUploadedFile("empty.pdf", b"fake pdf content"),
            original_filename="empty.pdf",
            extracted_text="",
        )
        response = self.client.post(
            reverse("quizzes"),
            {
                "title": "Empty Text Quiz",
                "description": "",
                "difficulty": "medium",
                "num_questions": 5,
                "question_types": ["multiple_choice"],
                "source_choice": "existing",
                "existing_pdf": [empty_file.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Quiz.objects.filter(user=self.user, title="Empty Text Quiz").exists())


# ----------------Tests for Matching Question Fix---------------------


class CheckAnswerMatchingTest(TestCase):
    """Tests for the matching question fix in check_answer()"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser_matching", password="testpass123"
        )
        self.quiz = Quiz.objects.create(user=self.user, title="Matching Quiz")
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_text="Match the terms:",
            question_type="matching",
            correct_answer="",
            pairs=[
                {"premise": "Photosynthesis", "response": "converts sunlight to energy"},
                {"premise": "Mitosis", "response": "cell division process"},
                {"premise": "Osmosis", "response": "movement of water across membrane"},
            ],
            order=1,
        )

    def test_all_correct_pairs(self):
        """All pairs matched correctly should return True"""
        user_answer = (
            "photosynthesis → converts sunlight to energy | "
            "mitosis → cell division process | "
            "osmosis → movement of water across membrane"
        )
        self.assertTrue(check_answer(self.question, user_answer))

    def test_all_wrong_pairs(self):
        """All pairs wrong should return False"""
        user_answer = (
            "photosynthesis → cell division process | "
            "mitosis → movement of water across membrane | "
            "osmosis → converts sunlight to energy"
        )
        self.assertFalse(check_answer(self.question, user_answer))

    def test_partial_correct_pairs(self):
        """Some pairs correct, some wrong should return False"""
        user_answer = (
            "photosynthesis → converts sunlight to energy | "
            "mitosis → movement of water across membrane | "  # wrong
            "osmosis → cell division process"  # wrong
        )
        self.assertFalse(check_answer(self.question, user_answer))

    def test_empty_answer_returns_false(self):
        """Empty answer should return False"""
        self.assertFalse(check_answer(self.question, ""))

    def test_missing_arrow_returns_false(self):
        """Malformed answer without → should return False"""
        user_answer = "photosynthesis | mitosis | osmosis"
        self.assertFalse(check_answer(self.question, user_answer))

    def test_wrong_number_of_pairs_returns_false(self):
        """Fewer pairs than expected should return False"""
        user_answer = "photosynthesis → converts sunlight to energy"
        self.assertFalse(check_answer(self.question, user_answer))

    def test_case_insensitive_matching(self):
        """Matching should be case insensitive"""
        user_answer = (
            "PHOTOSYNTHESIS → CONVERTS SUNLIGHT TO ENERGY | "
            "MITOSIS → CELL DIVISION PROCESS | "
            "OSMOSIS → MOVEMENT OF WATER ACROSS MEMBRANE"
        )
        self.assertTrue(check_answer(self.question, user_answer))
