# main/views.py

import json
import openai
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from .models import UserPrompt
from account.models import UserProfile

logger = logging.getLogger(__name__)

# **Note:** It's recommended to move the API key to environment variables.
openai.api_key = "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"

@require_POST
@csrf_protect
@login_required
def chat(request):
    """
    Handles POST requests:
      - Receives JSON data with 'message'
      - Sends it to OpenAI's GPT model
      - Saves and returns updated chat log + generated HTML
    """
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"error": "No message provided."}, status=400)

        # Check if user is exempt from prompt limits
        try:
            is_exempt = request.user.profile.is_exempt_from_prompt_limit
        except UserProfile.DoesNotExist:
            is_exempt = False  # Default to not exempt

        # If not exempt, enforce prompt limits
        if not is_exempt:
            today = timezone.now().date()
            user_prompt, created = UserPrompt.objects.get_or_create(user=request.user, date=today)
            if user_prompt.count >= settings.MAX_PROMPTS_PER_DAY:
                return JsonResponse({
                    "error": "Daily prompt limit reached. Please try again tomorrow.",
                    "remaining_prompts": 0
                }, status=403)

        # Initialize session data if not present
        chat_log = request.session.get("chat_log", [])
        website_html = request.session.get("website_html", "")

        # Add user message to chat log
        chat_log.append({"role": "user", "content": user_message})

        # Construct system prompt for generating HTML
        system_prompt = (
            "You are a helpful AI that generates HTML/CSS/JS for a website, using Bootstrap to create a powerful and great design.\n\n"
            f"User's request: {user_message}\n\n"
            "Please ONLY return the complete HTML code. No explanations."
        )

        # Call OpenAI's ChatCompletion endpoint with the correct model
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  
                messages=[
                    {"role": "system", "content": "You are a website-building assistant."},
                    {"role": "user", "content": system_prompt},
                ],
                temperature=0.7,
            )
            # Extract the AI's generated text
            ai_html = response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            ai_html = f"<!-- Error calling OpenAI API: {str(e)} -->"
            return JsonResponse({
                "error": "Failed to generate website content.",
                "details": str(e)
            }, status=500)

        # Add the assistant's reply to the chat log
        chat_log.append({"role": "assistant", "content": ai_html})

        # Update the entire website_html with the new HTML
        website_html = ai_html

        # If user is not exempt, increment the prompt count
        if not is_exempt:
            user_prompt.count += 1
            user_prompt.save()
            remaining_prompts = settings.MAX_PROMPTS_PER_DAY - user_prompt.count
        else:
            remaining_prompts = "Unlimited"

        # Save back to session
        request.session["chat_log"] = chat_log
        request.session["website_html"] = website_html
        request.session.modified = True

        # Respond with the assistant's reply and website HTML
        return JsonResponse({
            "reply": ai_html,
            "website_html": website_html,
            "remaining_prompts": remaining_prompts
        })
    except json.JSONDecodeError:
        logger.error("Invalid JSON received in chat view.", exc_info=True)
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in chat view: {str(e)}", exc_info=True)
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)

def home(request):
    """
    Renders the ChatGPT-like interface.
    Left side: chat
    Right side: generated website
    """
    if "chat_log" not in request.session:
        request.session["chat_log"] = []
    if "website_html" not in request.session:
        request.session["website_html"] = "<h2>Welcome!</h2><p>Let's build your site!</p>"
    return render(request, "main/home.html", {
        "chat_log": request.session["chat_log"],
        "website_html": request.session["website_html"],
    })


# Home view for all users
def home_view(request):
    return render(request, 'main/home.html')

# Chat view only accessible for logged-in users
@login_required(login_url='/account/login/')  # Redirect to login if not logged in
def chat_view(request):
    return render(request, 'main/chat.html')  # Create a 'chat.html' template if needed
