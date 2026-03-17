from behave import given, when, then
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from knowledge_app.models import UploadedFile
import os

# ---- Navigation scenario ----

@given('I am on the home page')
def step_on_home_page(context):
    # Visit the homepage
    context.response = context.client.get(reverse('homepage'))

@when('I click Upload Content in the sidebar')
def step_click_upload_in_sidebar(context):
    # Visit the upload page (simulates clicking the sidebar link)
    context.response = context.client.get(reverse('upload'))

@then('I should be taken to the upload page')
def step_taken_to_upload_page(context):
    # Confirm the upload page loaded successfully
    assert context.response.status_code == 200

# ---- Upload scenario ----

@given('I am on the upload page')
def step_on_upload_page(context):
    # Visit the upload page and confirm it loads
    context.response = context.client.get(reverse('upload'))
    assert context.response.status_code == 200

@when('I select a PDF file and click Upload')
def step_upload_pdf(context):
    # Create a fake PDF and submit the upload form
    pdf = SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
    context.response = context.client.post(reverse('upload'), {'pdf_file': pdf})

@then('the file should be saved and visible in the uploaded files list')
def step_file_saved_and_visible(context):
    # Confirm file was saved to database and appears on the page
    assert UploadedFile.objects.count() == 1
    response = context.client.get(reverse('upload'))
    assert b"test.pdf" in response.content

# ---- View previously uploaded files scenario ----

@when('I have uploaded files in the past')
def step_files_uploaded_in_past(context):
    # Upload a fake PDF to simulate a past upload
    pdf = SimpleUploadedFile("old.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
    context.client.post(reverse('upload'), {'pdf_file': pdf})

@then('I should see a list of all previously uploaded files')
def step_see_list_of_files(context):
    # Confirm the uploaded file appears in the list on the page
    response = context.client.get(reverse('upload'))
    assert b"old.pdf" in response.content

# ---- Delete scenario ----

@given('there is at least one file in the list')
def step_file_in_list(context):
    # Upload a fake PDF so there is something to delete
    pdf = SimpleUploadedFile("delete_me.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
    context.client.post(reverse('upload'), {'pdf_file': pdf})
    context.uploaded = UploadedFile.objects.first()  # save reference for later

@when('I click Delete on a file')
def step_click_delete(context):
    # Save the file path then send a delete request
    context.file_path = context.uploaded.file.path
    context.client.post(reverse('delete_file', args=[context.uploaded.id]))

@then('the file should be removed from the list and deleted from storage')
def step_file_removed(context):
    # Confirm file is gone from database and disk
    assert UploadedFile.objects.count() == 0
    assert not os.path.exists(context.file_path)