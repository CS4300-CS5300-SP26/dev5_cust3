from behave import given, when, then
from django.urls import reverse
from django.contrib.auth.models import User
from knowledge_app.models import Quiz
from unittest.mock import patch

@given('I am logged in')
def step_logged_in(context):
    context.user = User.objects.create_user(username='testuser', password='testpass123')
    context.client.login(username='testuser', password='testpass123')

@when('I visit the quizzes page')
def step_visit_quizzes(context):
    context.response = context.client.get(reverse('quizzes'))

@then('I should see the quiz generation form')
def step_see_form(context):
    assert context.response.status_code == 200
    assert b'Generate' in context.response.content

@then('I should see the existing PDF option')
def step_see_existing_option(context):
    assert b'existing' in context.response.content

@then('I should see the upload PDF option')
def step_see_upload_option(context):
    assert b'upload' in context.response.content

@then('I should see the paste text option')
def step_see_text_option(context):
    assert b'text' in context.response.content

from unittest.mock import patch

@when('I submit the quiz form with text input')
def step_submit_text_quiz(context):
    # Mock the OpenAI call so tests don't need a real API key
    with patch('knowledge_app.views.generate_quiz_from_text'):
        context.response = context.client.post(reverse('quizzes'), {
            'title': 'Test Quiz',
            'description': 'A test quiz',
            'difficulty': 'medium',
            'num_questions': 3,
            'question_types': ['multiple_choice'],
            'source_choice': 'text',
            'text_input': 'The CPU processes instructions. RAM is volatile memory.'
        })

@then('a new quiz should be created')
def step_quiz_created(context):
    # Confirm a quiz record was created in the database
    assert Quiz.objects.filter(user=context.user).count() == 1