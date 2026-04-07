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

# Stores a map generated from an uploaded PDF
class KnowledgeMap(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.title

# Topic cluster
class TopicNode(models.Model):
    knowledge_map = models.ForeignKey(KnowledgeMap, on_delete=models.CASCADE, related_name='topics')
    label = models.CharField(max_length=255)        #to be given from OpenAI
    summary = models.TextField()                    # summary from OpenAI
    x_position = models.FloatField(default=0)       # map position
    y_position = models.FloatField(default=0)

    def __str__(self):
        return self.label

# Subtopic under a topic node
class SubtopicNode(models.Model):
    topic = models.ForeignKey(TopicNode, on_delete=models.CASCADE, related_name='subtopics')
    label = models.CharField(max_length=255)
    summary = models.TextField()
    x_position = models.FloatField(default=0)
    y_position = models.FloatField(default=0)

    def __str__(self):
        return self.label

# Relationship/edge between two topic nodes on the map
class NodeRelationship(models.Model):
    knowledge_map = models.ForeignKey(KnowledgeMap, on_delete=models.CASCADE, related_name='relationships')
    source_topic = models.ForeignKey(TopicNode, on_delete=models.CASCADE, related_name='outgoing')
    target_topic = models.ForeignKey(TopicNode, on_delete=models.CASCADE, related_name='incoming')
    relationship_label = models.CharField(max_length=255)   # e.g. "relates to", "leads to"

    def __str__(self):
        return f"{self.source_topic} → {self.target_topic}"