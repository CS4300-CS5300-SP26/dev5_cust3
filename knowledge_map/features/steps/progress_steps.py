from behave import given, when, then
from django.urls import reverse
from django.contrib.auth.models import User
from knowledge_app.models import Quiz, Question, QuizAttempt


@when('I visit the progress page')
def step_visit_progress(context):
    context.response = context.client.get(reverse('progress'))


@then('I should see the mastery progress page')
def step_see_progress_page(context):
    assert context.response.status_code == 200
    assert b'Mastery Progress' in context.response.content


@given('I have a quiz with no attempts')
def step_quiz_no_attempts(context):
    context.quiz = Quiz.objects.create(
        user=context.user,
        title='Test Quiz',
        difficulty='medium'
    )


@then('I should see the not attempted status')
def step_see_not_attempted(context):
    assert b'Not Started' in context.response.content


@given('I have a quiz with a score of 80')
def step_quiz_score_80(context):
    quiz = Quiz.objects.create(
        user=context.user,
        title='Mastered Quiz',
        difficulty='easy'
    )
    QuizAttempt.objects.create(
        quiz=quiz,
        user=context.user,
        score=80,
        correct_count=4,
        total_questions=5
    )


@then('I should see the mastered status')
def step_see_mastered(context):
    assert b'Mastered' in context.response.content