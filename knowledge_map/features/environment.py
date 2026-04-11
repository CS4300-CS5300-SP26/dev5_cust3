import os
import django
from django.test import Client
from django.test.utils import setup_test_environment
from django.test.runner import DiscoverRunner



# Tell Django which settings file to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowledge_map.settings')

# Set up Django immediately when environment loads
django.setup()

def before_scenario(context, scenario):
    from django.contrib.auth.models import User
    context.client = Client()
    context.user = User.objects.create_user(
        username='testuser',
        password='testpass123'
    )
    context.client.login(username='testuser', password='testpass123')

def before_all(context):
    # Set up test environment once before all scenarios
    setup_test_environment()
    context.test_runner = DiscoverRunner(verbosity=0)
    # Create + migrate a test database
    context.old_db_config = context.test_runner.setup_databases()
    context.client = Client()

# Destroy the test database
def after_all(context):
    context.test_runner.teardown_databases(context.old_db_config)

def after_scenario(context, scenario):
    # Clean up any uploaded test files after each scenario
    from knowledge_app.models import UploadedFile
    import os
    for f in UploadedFile.objects.all():
        if os.path.exists(f.file.path):
            os.remove(f.file.path)
    UploadedFile.objects.all().delete()

    # Clean up any users after each scenario
    from django.contrib.auth.models import User
    User.objects.all().delete()