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

# Set your OpenAI API key (using your pinned version)
openai.api_key = "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"

@require_POST
@csrf_protect
@login_required
def chat(request):
    """
    Handles the AJAX POST request:
      1. Reads the user's message.
      2. Calls OpenAI to build or modify the website.
      3. Returns valid JSON with 'reply' and 'website_code'.
    """
    # Parse the request body safely.
    try:
        data = json.loads(request.body)
    except Exception as e:
        logger.error("Failed to parse request body: " + str(e), exc_info=True)
        return JsonResponse({"error": "Invalid request format."}, status=400)

    user_message = data.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "No message provided."}, status=400)

    # Check if the user is exempt from daily prompt limits.
    try:
        is_exempt = request.user.profile.is_exempt_from_prompt_limit
    except UserProfile.DoesNotExist:
        is_exempt = False

    if not is_exempt:
        today = timezone.now().date()
        user_prompt, _ = UserPrompt.objects.get_or_create(user=request.user, date=today)
        if user_prompt.count >= settings.MAX_PROMPTS_PER_DAY:
            return JsonResponse({
                "error": "Daily prompt limit reached. Please try again tomorrow.",
                "remaining_prompts": 0
            }, status=403)

    # Retrieve the current website from session (if any)
    current_html = request.session.get("website_html", "")
    has_website = bool(current_html.strip())

    # Record the conversation in the session.
    chat_log = request.session.get("chat_log", [])
    chat_log.append({"role": "user", "content": user_message})

    # Improved system prompt for interactive modern website design using Bootstrap 5.
    system_prompt = """
You are Helios, an advanced website-building assistant dedicated to creating modern, visually appealing, and highly responsive websites using the latest frameworks and design practices. Your task is to interact directly with the user to fully understand their website requirements by asking clarifying questions if necessary, and then produce complete, production-ready website code.

When a user provides instructions, you MUST:
1. Ask clarifying questions if any part of the request is ambiguous. In your "conversation" field, include a concise summary of your clarifications and design decisions.
2. Generate complete, self-contained website code that starts with <!DOCTYPE html> and includes all necessary HTML, CSS, and JavaScript. Use modern frameworks like Bootstrap 5 to ensure the design is responsive and attractive, incorporating interactive elements (e.g., navigation bars, modals, carousels, and subtle animations) where appropriate.
3. Return ONLY valid JSON enclosed within triple backticks (```), with no extra text or markdown. The JSON MUST have exactly two keys:
   - "conversation": A plain text summary of your clarifications and design decisions.
   - "website_code": The full, updated website code.

Do not output anything outside the triple backticks.

Example output:
{ "conversation": "Based on the user's request for a modern mobile app landing page, I clarified the need for a bold hero section with an app preview, detailed feature sections, clear pricing tiers, and download buttons for iOS and Android. I implemented a responsive design using Bootstrap 5 and added subtle animations.", "website_code": "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'><title>Mobile App Landing</title></head><body><nav class='navbar navbar-expand-lg navbar-dark bg-dark'><a class='navbar-brand' href='#'>App Landing</a></nav><div class='container mt-4'><div class='row'><div class='col-md-6'>Feature Section 1</div><div class='col-md-6'>Feature Section 2</div></div></div><script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'></script></body></html>" }""".strip()

    # Build the messages list based on whether an existing website exists.
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

    # Call OpenAI and process the response.
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages_list,
            temperature=0.2,  # Lower temperature for more deterministic output.
        )
        raw_content = response["choices"][0]["message"]["content"]
        logger.debug(f"OpenAI raw response: {raw_content}")

        # Extract JSON enclosed in triple backticks if present.
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
        # Fallback: provide a formatted error message.
        ai_reply = "Helios: Sorry, I couldn't generate the correct format."
        updated_html = current_html

    # Update session with chat log and website code.
    chat_log.append({"role": "assistant", "content": ai_reply})
    request.session["chat_log"] = chat_log
    request.session["website_html"] = updated_html
    request.session.modified = True

    # Update prompt count if not exempt.
    if not is_exempt:
        user_prompt.count += 1
        user_prompt.save()
        remaining_prompts = settings.MAX_PROMPTS_PER_DAY - user_prompt.count
    else:
        remaining_prompts = "Unlimited"

    return JsonResponse({
        "reply": ai_reply,
        "website_code": updated_html,
        "remaining_prompts": remaining_prompts
    })

def home(request):
    if "chat_log" not in request.session:
        request.session["chat_log"] = []
    if "website_html" not in request.session:
        request.session["website_html"] = "<h2>Welcome!</h2><p>Let's build your site!</p>"
    return render(request, "main/home.html", {
        "chat_log": request.session["chat_log"],
        "website_html": request.session["website_html"],
    })

def home_view(request):
    return render(request, 'main/home.html')

@login_required(login_url='/account/login/')
def chat_view(request):
    return render(request, 'main/chat.html')
