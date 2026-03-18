from behave import given, when, then
from django.contrib.auth.models import User
from django.urls import reverse

@given('I am on the registration page')
def step_visit_register(context):
    context.response = context.client.get(reverse('register'))


@given('I am on the login page')
def step_visit_login(context):
    context.response = context.client.get(reverse('login'))


@given('a user already exists with username "{username}" and password "{password}"')
def step_user_exists_with_password(context, username, password):
    User.objects.create_user(username=username, password=password)


@given('I am logged in as "{username}" with password "{password}"')
def step_logged_in(context, username, password):
    User.objects.filter(username=username).delete() 
    user = User.objects.create_user(username=username, password=password)
    context.client.login(username=username, password=password)


@given('I am not logged in')
def step_not_logged_in(context):
    context.client.logout()


@when('I register with username "{username}" and password "{password}"')
def step_register(context, username, password):
    context.response = context.client.post(
        reverse('register'),
        {'username': username, 'password': password},
        follow=True
    )


@when('I login with username "{username}" and password "{password}"')
def step_login(context, username, password):
    context.response = context.client.post(
        reverse('login'),
        {'username': username, 'password': password},
        follow=True
    )


@when('I log out')
def step_logout(context):
    context.response = context.client.post(reverse('logout'), follow=True)


@then('I should be redirected to the home page')
def step_redirected_to_home(context):
    assert context.response.status_code == 200
    # Check we landed on the home page by looking for known content
    assert 'KnowledgeMap' in context.response.content.decode(), \
        f'Expected to be on home page but got: {context.response.content.decode()[:200]}'


@then('I should be redirected to the login page')
def step_redirected_to_login(context):
    assert context.response.status_code == 200
    assert 'Log In' in context.response.content.decode(), \
        f'Expected to be on login page but got: {context.response.content.decode()[:200]}'


@then('I should be logged in')
def step_should_be_logged_in(context):
    assert '_auth_user_id' in context.client.session


@then('I should not be logged in')
def step_should_not_be_logged_in(context):
    assert '_auth_user_id' not in context.client.session


@then('I should see "{text}"')
def step_see_text(context, text):
    assert text in context.response.content.decode(), \
        f'Expected "{text}" in response but got: {context.response.content.decode()[:200]}'