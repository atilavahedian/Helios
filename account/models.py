# account/models.py

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_exempt_from_prompt_limit = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"
