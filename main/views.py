import json
import re
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

# Ensure the API key is set (using your pinned version of openai)
openai.api_key = "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"

@require_POST
@csrf_protect
@login_required
def chat(request):
    """
    Handles the AJAX POST request from the frontend:
      1. Reads user message.
      2. Calls OpenAI to build or modify the website.
      3. Returns JSON with 'reply' and 'website_html'.
    """
    # Parse request body safely
    try:
        data = json.loads(request.body)
    except Exception as e:
        logger.error("Failed to parse request body: " + str(e), exc_info=True)
        return JsonResponse({"error": "Invalid request format."}, status=400)

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
    has_website = bool(current_html.strip())

    # Record the conversation in session
    chat_log = request.session.get("chat_log", [])
    chat_log.append({"role": "user", "content": user_message})

    # Updated system prompt for best website generation
    system_prompt = """
You are Helios, an advanced website-building assistant focused on crafting modern, visually appealing, and high-quality websites. 
The user will provide instructions for building or modifying a website.
You MUST return ONLY valid JSON, with no extra text or markdown, enclosed within triple backticks (```).
The JSON must contain exactly two keys:
  - "conversation": A plain text summary of the changes you made.
  - "website_code": The complete, updated HTML/CSS/JS code for the website.
Do not output anything else outside the triple backticks.
Example output:
{ "conversation": "Updated the homepage layout and added animations.", "website_code": "<!DOCTYPE html><html> ... </html>" }""".strip()

    # Build messages list based on whether an existing website exists
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

    # Call OpenAI and process the response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Using your specified model name
            messages=messages_list,
            temperature=0.5,      # Lower temperature for more deterministic output
        )
        raw_content = response["choices"][0]["message"]["content"]
        logger.debug(f"OpenAI raw response: {raw_content}")

        # Extract JSON enclosed in triple backticks if present
        json_match = re.search(r"```(.*?)```", raw_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = raw_content.strip()

        parsed = json.loads(json_str)
        ai_reply = parsed.get("conversation", "")
        updated_html = parsed.get("website_code", "")
        if not ai_reply or not updated_html:
            raise ValueError("Missing expected keys in response")
    except Exception as e:
        logger.error("OpenAI API error or response parsing error: " + str(e), exc_info=True)
        # Fallback messages
        ai_reply = "Helios: Sorry, I couldn't generate the correct format."
        updated_html = current_html

    # Append AI response to chat log and update session
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
