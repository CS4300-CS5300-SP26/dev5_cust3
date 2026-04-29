from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# Database table - stores info about PDF uploads
# add folders model
class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']  # no duplicate folder names per user


class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='uploaded_files', null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    extracted_text = models.TextField(blank=True, default='')
    folder = models.ForeignKey(Folder, null=True, blank=True,   # update for folders
                               on_delete=models.SET_NULL,
                               related_name='files')

    @property
    def display_name(self):
        return self.original_filename or self.file.name

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['-uploaded_at']


class Quiz(models.Model):
    """Main quiz model"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Reference to your existing UploadedFile model
    source_file = models.ForeignKey(
        'UploadedFile',  # Your existing model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_quizzes'
    )
    source_text = models.TextField(blank=True)  # If generated from text input

    # Quiz settings
    difficulty = models.CharField(
        max_length=20,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def latest_attempt(self):
        return self.attempts.order_by('-created_at').first()

    @property
    def total_attempts(self):
        return self.attempts.count()

    @property
    def average_score(self):
        attempts = self.attempts.all()
        if not attempts.exists():
            return None
        total_score = sum(attempt.score for attempt in attempts)
        return round(total_score / attempts.count(), 2)


class Question(models.Model):
    """Quiz question model"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('fill_in_blank', 'Fill in the Blank'),
        ('true_false', 'True/False'),
        ('matching', 'Matching'),
        ('short_answer', 'Short Answer'),
    ]

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)

    # For multiple choice and fill in blank
    choices = models.JSONField(default=list, blank=True)  # List of choices
    correct_answer = models.TextField()  # The correct answer

    # For matching questions
    # [{"premise": "...", "response": "..."}]
    pairs = models.JSONField(default=list, blank=True)

    # Metadata
    order = models.PositiveIntegerField(default=0)  # Order in quiz
    explanation = models.TextField(blank=True)  # Optional explanation

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quiz', 'order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}: {self.question_text[:50]}"


class QuizAttempt(models.Model):
    """Track each time a user takes a quiz"""
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='quiz_attempts')

    # Scoring
    score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # Percentage score
    correct_count = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.score}%)"

    @property
    def accuracy_percentage(self):
        return self.score


class Answer(models.Model):
    """Individual answer for a question in an attempt"""
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers')

    user_answer = models.TextField()
    correct_answer = models.TextField()
    is_correct = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt} - Q{self.question.order}: {'✓' if self.is_correct else '✗'}"


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
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.title

# Topic cluster


class TopicNode(models.Model):
    knowledge_map = models.ForeignKey(
        KnowledgeMap, on_delete=models.CASCADE, related_name='topics')
    label = models.CharField(max_length=255)  # to be given from OpenAI
    summary = models.TextField()                    # summary from OpenAI
    x_position = models.FloatField(default=0)       # map position
    y_position = models.FloatField(default=0)

    def __str__(self):
        return self.label

# Subtopic under a topic node


class SubtopicNode(models.Model):
    topic = models.ForeignKey(
        TopicNode, on_delete=models.CASCADE, related_name='subtopics')
    label = models.CharField(max_length=255)
    summary = models.TextField()
    x_position = models.FloatField(default=0)
    y_position = models.FloatField(default=0)

    def __str__(self):
        return self.label

# Relationship/edge between two topic nodes on the map
class NodeRelationship(models.Model):
    knowledge_map = models.ForeignKey(
        KnowledgeMap, on_delete=models.CASCADE, related_name='relationships')
    source_topic = models.ForeignKey(
        TopicNode, on_delete=models.CASCADE, related_name='outgoing')
    target_topic = models.ForeignKey(
        TopicNode, on_delete=models.CASCADE, related_name='incoming')
    relationship_label = models.CharField(
        max_length=255)   # e.g. "relates to", "leads to"

    def __str__(self):
        return f"{self.source_topic} → {self.target_topic}"

# User profile to persist personal settings
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    dark_mode = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


# Django signals to ensure that every user will get a profile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

    
# store permissions for a knowledge map
class SharedMap(models.Model):
    knowledge_map = models.ForeignKey(KnowledgeMap, on_delete=models.CASCADE, related_name='shares')

    # public link sharing - anyone with the token can view
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_public = models.BooleanField(default=False)

    # sharing with specific user
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='shared_map')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.shared_with:
            return f"{self.knowledge_map.title} shared with {self.shared_with.username}"
        return f"{self.knowledge_map.title} (public link)"

# Stores a custom map built by the user on the homepage
class CustomMap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_maps')
    title = models.CharField(max_length=255, default='Untitled Map')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"

# A node in a custom map
class CustomNode(models.Model):
    custom_map = models.ForeignKey(CustomMap, on_delete=models.CASCADE, related_name='nodes')
    label = models.CharField(max_length=255)
    summary = models.TextField(blank=True, default='')
    x_position = models.FloatField(default=0)
    y_position = models.FloatField(default=0)

    def __str__(self):
        return self.label

# An edge in a custom map
class CustomEdge(models.Model):
    custom_map = models.ForeignKey(CustomMap, on_delete=models.CASCADE, related_name='edges')
    source = models.ForeignKey(CustomNode, on_delete=models.CASCADE, related_name='outgoing')
    target = models.ForeignKey(CustomNode, on_delete=models.CASCADE, related_name='incoming')
    label = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.source} → {self.target}"
