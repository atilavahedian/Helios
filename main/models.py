# main/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserPrompt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompts')
    date = models.DateField(default=timezone.now)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')
        verbose_name = 'User Prompt'
        verbose_name_plural = 'User Prompts'

    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.count} prompts"

class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']  # Orders messages chronologically

    def __str__(self):
        return f"{self.user.username} - {self.sender} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class Website(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='website')
    html_content = models.TextField(default="<h2>Welcome!</h2><p>Let's build your site!</p>")
    slug = models.SlugField(unique=True, max_length=50, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Website"
