# account/admin.py

from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_exempt_from_prompt_limit', 'prompt_limit')  
    list_filter = ('is_exempt_from_prompt_limit', 'prompt_limit', 'user')  
    search_fields = ('user__username', 'user__email')
    list_editable = ('is_exempt_from_prompt_limit', 'prompt_limit')
