import os
import django

# Tell Django which settings file to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowledge_map.settings')

# Set up Django immediately when environment loads
django.setup()

def before_all(context):
    # Set up test environment once before all scenarios
    from django.test.utils import setup_test_environment
    setup_test_environment()

def before_scenario(context, scenario):
    # Set up a fake browser client before each scenario
    from django.test import Client
    context.client = Client()

def after_scenario(context, scenario):
    # Clean up any uploaded test files after each scenario
    from knowledge_app.models import UploadedFile
    import os
    for f in UploadedFile.objects.all():
        if os.path.exists(f.file.path):
            os.remove(f.file.path)
    UploadedFile.objects.all().delete()