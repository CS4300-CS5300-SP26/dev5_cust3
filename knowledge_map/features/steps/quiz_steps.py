from unittest.mock import patch

from behave import given, then, when
from django.contrib.auth.models import User
from django.urls import reverse

from knowledge_app.models import Quiz


@given("I am logged in")
def step_logged_in(context):
    context.user, _ = User.objects.get_or_create(
        username="testuser", defaults={"password": "testpass123"}
    )
    context.client.login(username="testuser", password="testpass123")


@when("I visit the quizzes page")
def step_visit_quizzes(context):
    context.response = context.client.get(reverse("quizzes"))


@then("I should see the quiz generation form")
def step_see_form(context):
    assert context.response.status_code == 200
    assert b"Generate" in context.response.content


@then("I should see the existing PDF option")
def step_see_existing_option(context):
    assert b"existing" in context.response.content


@then("I should see the upload PDF option")
def step_see_upload_option(context):
    assert b"upload" in context.response.content


@then("I should see the paste text option")
def step_see_text_option(context):
    assert b"text" in context.response.content


@when("I submit the quiz form with text input")
def step_submit_text_quiz(context):
    from knowledge_app.models import Question
    with patch("knowledge_app.views.generate_quiz_from_text") as mock_gen:
        # Simulate questions being created so quiz isn't deleted
        def fake_generate(quiz, **kwargs):
            Question.objects.create(
                quiz=quiz,
                question_text="Test question?",
                question_type="multiple_choice",
                choices=["a", "b", "c", "d"],
                correct_answer="a",
                order=1,
            )
        mock_gen.side_effect = fake_generate
        context.response = context.client.post(
            reverse("quizzes"),
            {
                "title": "Test Quiz",
                "description": "A test quiz",
                "difficulty": "medium",
                "num_questions": 3,
                "question_types": ["multiple_choice"],
                "source_choice": "text",
                "text_input": "The CPU processes instructions. RAM is volatile memory.",
            },
        )


@then("a new quiz should be created")
def step_quiz_created(context):
    # Confirm a quiz record was created in the database
    assert Quiz.objects.filter(user=context.user).count() == 1
