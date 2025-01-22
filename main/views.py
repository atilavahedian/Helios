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


openai.api_key = "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"

@require_POST
@csrf_protect
@login_required
def chat(request):
    """
    Handles the AJAX POST request from the frontend:
      1. Reads user message
      2. Calls OpenAI to build or modify the website
      3. Returns JSON with 'reply' and 'website_html'
    """
    data = json.loads(request.body)
    user_message = data.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "No message provided."}, status=400)

    # Check if user is exempt from daily prompt limits.
    try:
        is_exempt = request.user.profile.is_exempt_from_prompt_limit
    except UserProfile.DoesNotExist:
        is_exempt = False

    # Enforce daily prompt limit if not exempt
    if not is_exempt:
        today = timezone.now().date()
        user_prompt, _ = UserPrompt.objects.get_or_create(user=request.user, date=today)
        if user_prompt.count >= settings.MAX_PROMPTS_PER_DAY:
            return JsonResponse({
                "error": "Daily prompt limit reached. Please try again tomorrow.",
                "remaining_prompts": 0
            }, status=403)

    # Retrieve existing website from session
    current_html = request.session.get("website_html", "")
    has_website = bool(current_html.strip())  # True if we already have some website code

    # Record the conversation in session
    chat_log = request.session.get("chat_log", [])
    chat_log.append({"role": "user", "content": user_message})


    system_prompt = """
    You are Helios, an advanced website-building assistant focusing on modern, visually appealing web design. 
    The user will provide instructions about building or modifying a website.

    You MUST return valid JSON with exactly two keys:
    1) "conversation": plain text only (no code blocks)
    2) "website_code": the updated HTML/CSS/JS, preferably using too much Bootstrap  
    and any modern styling/animations for a polished look.

    Important:
    - If 'has_website' is True, incorporate or refine the existing code in your new website_code.
    - If 'has_website' is False, create a brand-new site from scratch with a well-structured layout and contemporary design.
    - DO NOT include any code in the "conversation" field. All code must go in "website_code."

    Example of the required output:

    {
    "conversation": "Here is a concise overview of the changes I made...",
    "website_code": "<!DOCTYPE html><html> ... your updated or newly created site ... </html>"
    }
    """.strip()


    # Decide how to feed the model
    if has_website:
        messages_list = [
            {"role": "system", "content": system_prompt},
            {
                "role": "assistant",
                "content": f"Existing website code:\n{current_html}"
            },
            {"role": "user", "content": user_message},
        ]
    else:
        messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    # Call OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Using the specified model name
            messages=messages_list,
            temperature=0.7,
        )
        raw_content = response["choices"][0]["message"]["content"]
        logger.debug(f"OpenAI raw response: {raw_content}")  # Log the raw JSON/text for debugging

        # Attempt to parse the model's JSON
        try:
            parsed = json.loads(raw_content)
            ai_reply = parsed.get("conversation", "")
            updated_html = parsed.get("website_code", "")
        except Exception:
            # If the model didn't return valid JSON or missing keys
            ai_reply = "Helios: Sorry, I couldn't generate the correct format."
            updated_html = current_html

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Failed to generate website content."}, status=500)

    # Append AI response to chat
    chat_log.append({"role": "assistant", "content": ai_reply})
    request.session["chat_log"] = chat_log
    request.session["website_html"] = updated_html
    request.session.modified = True

    # Update prompt count if not exempt
    if not is_exempt:
        user_prompt.count += 1
        user_prompt.save()
        remaining_prompts = settings.MAX_PROMPTS_PER_DAY - user_prompt.count
    else:
        remaining_prompts = "Unlimited"

    # Return final JSON
    return JsonResponse({
        "reply": ai_reply,
        "website_html": updated_html,
        "remaining_prompts": remaining_prompts
    })


def home(request):
    """
    Renders the chat + website interface.
    Initializes session data if not present.
    """
    if "chat_log" not in request.session:
        request.session["chat_log"] = []
    if "website_html" not in request.session:
        request.session["website_html"] = "<h2>Welcome!</h2><p>Let's build your site!</p>"

    return render(request, "main/home.html", {
        "chat_log": request.session["chat_log"],
        "website_html": request.session["website_html"],
    })


def home_view(request):
    """
    Simple home view if needed.
    """
    return render(request, 'main/home.html')


@login_required(login_url='/account/login/')
def chat_view(request):
    """
    A dedicated chat view if desired.
    """
    return render(request, 'main/chat.html')
