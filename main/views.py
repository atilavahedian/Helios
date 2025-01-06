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
    data = json.loads(request.body)
    user_message = data.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "No message provided."}, status=400)

    try:
        is_exempt = request.user.profile.is_exempt_from_prompt_limit
    except UserProfile.DoesNotExist:
        is_exempt = False

    if not is_exempt:
        today = timezone.now().date()
        user_prompt, _ = UserPrompt.objects.get_or_create(user=request.user, date=today)
        if user_prompt.count >= settings.MAX_PROMPTS_PER_DAY:
            return JsonResponse({"error": "Daily prompt limit reached. Please try again tomorrow.",
                                 "remaining_prompts": 0}, status=403)

    # Retrieve existing website HTML from session if available
    current_html = request.session.get("website_html", "")

    # Build or Modify Decision
    # We'll store a simple flag in the session, e.g. "has_website" to decide whether to modify or build new
    has_website = bool(current_html.strip())

    chat_log = request.session.get("chat_log", [])
    chat_log.append({"role": "user", "content": user_message})

    system_prompt = (
        "You are Helios, an advanced website-building assistant. The user will provide instructions about building or "
        "You are a helpful AI that generates HTML/CSS/JS for a website, using Bootstrap to create a powerful and great design.\n"
        "modifying a website. You MUST return a JSON object with exactly two keys:\n\n"
        "1) 'conversation': plain text only, no code.\n"
        "2) 'website_code': the updated HTML/CSS/JS.\n\n"
        "Important:\n"
        "- If 'has_website' is True, you only modify the existing HTML/CSS/JS.\n"
        "- If 'has_website' is False, you create a brand new website from scratch.\n"
        "- Never include any code in 'conversation'."
    )

    # Provide the current HTML as context if we already have a website
    if has_website:
        messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": f"Existing website code:\n{current_html}"},
            {"role": "user", "content": user_message},
        ]
    else:
        messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages_list,
            temperature=0.7,
        )
        raw_content = response["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(raw_content)
            ai_reply = parsed.get("conversation", "")
            updated_html = parsed.get("website_code", "")
        except:
            ai_reply = "Helios: Sorry, I couldn't generate the correct format."
            updated_html = current_html
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Failed to generate website content."}, status=500)

    chat_log.append({"role": "assistant", "content": ai_reply})
    request.session["chat_log"] = chat_log
    request.session["website_html"] = updated_html
    request.session.modified = True

    if not is_exempt:
        user_prompt.count += 1
        user_prompt.save()
        remaining_prompts = settings.MAX_PROMPTS_PER_DAY - user_prompt.count
    else:
        remaining_prompts = "Unlimited"

    return JsonResponse({
        "reply": ai_reply,
        "website_html": updated_html,
        "remaining_prompts": remaining_prompts
    })

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
