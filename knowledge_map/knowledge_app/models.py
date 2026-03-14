from django.db import models
from django.contrib.auth.models import User

# Database table - stores info about PDF uploads
class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    #Store user and extracted text
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    #extracts text for BERTopic
    extracted_text = models.TextField(blank=True, default='')

    def __str__(self):
        return self.file.name
