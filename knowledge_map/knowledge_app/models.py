from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json

# Database table - stores info about PDF uploads
class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    #Store user and extracted text
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    #extracts text for BERTopic
    extracted_text = models.TextField(blank=True, default='')

    def __str__(self):
        return self.file.name


    class Meta:
        ordering = ['-uploaded_at']

class Quiz(models.Model):
    """Main quiz model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
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
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    
    # For multiple choice and fill in blank
    choices = models.JSONField(default=list, blank=True)  # List of choices
    correct_answer = models.TextField()  # The correct answer
    
    # For matching questions
    pairs = models.JSONField(default=list, blank=True)  # [{"premise": "...", "response": "..."}]
    
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
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    
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
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    
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

