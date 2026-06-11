import google.generativeai as genai
import base64
import json
import time
import re

from backend.config import settings

MAX_RETRIES = 1
BASE_RETRY_DELAY = 2  # seconds

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def analyze_screenshot(
    image_bytes: bytes,
    user_rules: list[dict],
    user_instruction: str = "",
    previous_description: str = "",
    bg_context: str = ""
):
    """
    Analyze screenshot using Gemini Vision.
    """

    rules_text = ""

    if user_rules:
        rules_text = "\nUSER RULES:\n"

        for i, rule in enumerate(user_rules, start=1):
            rules_text += (
                f"{i}. {rule['name']} : {rule['prompt']}\n"
            )

    previous_text = ""

    if previous_description:
        previous_text = (
            f"\nPREVIOUS SCREEN STATE DESCRIPTION:\n{previous_description}\n"
        )

    bg_text = ""
    if bg_context:
        bg_text = (
            f"\nBACKGROUND SYSTEM CHANGES (for context only, DO NOT generate alerts from this):\n{bg_context}\n"
        )

    prompt = f"""
You are an AI Activity Monitoring System that detects EVERY small change on the user's screen and provides precise, human-readable activity reports.

Analyze this screenshot and describe what the user is currently doing.

CORE PRINCIPLES:
1. **Summary must describe the user's ACTUAL activity in plain language.**
   - GOOD examples: "The user is texting someone on WhatsApp", "The user is watching a YouTube video about cooking", "The user is writing Python code in VS Code", "The user is browsing Reddit", "The YouTube video is currently paused at 3:45", "The video has completed playing"
   - BAD examples: "Screenshot captured", "Multiple applications detected", "System state unchanged", "Screen activity detected"
   - The summary should read like a human observer describing what they see.
   - CRITICAL: If the USER RULES request specific analysis (e.g., "alert me if video stops", "analyze each tab"), your `summary` MUST explicitly include the results of that analysis (e.g., "Video is paused at 3:45. Multiple tabs are open: Tab 1 is Gmail, Tab 2 is YouTube").

2. **change_importance rating:**
   - "high": The user switched to a completely different activity (e.g., coding → watching video, or browsing → messaging)
   - "medium": Meaningful progress within the same activity (e.g., opened a new chat, switched browser tabs to a different website, started a new file, video paused/resumed, new notification appeared)
   - "low": No meaningful change from the previous state (e.g., still writing in the same document, same video still playing at nearly same position, minor cursor movements)

3. **Alerts — ONLY from user-defined rules (BE EXTREMELY SENSITIVE):**
   - ONLY generate alert objects for rules listed in the USER RULES section below.
   - If there are NO user rules, the "alerts" list MUST be empty.
   - Do NOT generate generic alerts about system processes, background apps, or screen activity.
   - Each alert must reference the exact rule_name from the USER RULES list.
   - **CRITICAL: Be extremely sensitive to rule matches.** If a user says "alert me if the video pauses" and you see a paused video, ALWAYS trigger the alert even if the change seems small. The user wants to know about EVERY occurrence.
   - **CRITICAL: The alert message must be written exactly in the context of what the user asked for.** For example, if the user's rule says "Alert me if the YouTube video stops", and the video is paused, the alert message should say something like "The YouTube video is currently paused" — NOT a generic system message.

MICRO-STATE DETECTION (VERY IMPORTANT):
- For VIDEO PLAYERS (YouTube, Netflix, VLC, etc.):
  * Detect play/pause button state (triangle = playing, two bars = paused)
  * Detect progress bar position and total duration
  * Detect if video has reached the end (progress bar full, replay button visible)
  * Detect if video is buffering (loading spinner)
  * Detect video title changes
- For BROWSERS:
  * Detect which tab is active
  * Detect if a new tab was opened or closed
  * Detect URL changes
  * Detect page loading states
  * Detect popup notifications or dialogs
- For MESSAGING APPS:
  * Detect new messages received
  * Detect typing indicators
  * Detect read/unread status
  * Detect if user is typing a response
- For CODE EDITORS:
  * Detect file changes (different filename in tab)
  * Detect if code is running (terminal output)
  * Detect error indicators
- For GENERAL:
  * Detect any notification popups (system tray, browser, app)
  * Detect window focus changes
  * Detect modal dialogs or confirmation boxes
  * Detect loading screens or progress bars

ANALYSIS INSTRUCTIONS:
{previous_text}
{bg_text}

- Identify the foreground application and what the user is doing in it.
- Detect visible applications, websites, browser tabs, coding tools, AI tools, social media, communication apps, video platforms.
- If multiple windows or split-screen are visible, describe each.
- For video players: note play/pause state, progress bar position, video title.
- For messaging apps: note if actively typing, reading messages, or just having the app open.
- Compare carefully with the PREVIOUS SCREEN STATE and note ANY differences, no matter how small.

USER RULES FOR ALERTS:
{rules_text}
{user_instruction}

ALERT GENERATION RULES:
1. ONLY generate alerts for rules explicitly listed in USER RULES above.
2. If a rule matches even partially, set "triggered": true and use the EXACT rule name as "rule_name".
3. **The alert "message" MUST be written based on the user's instruction tone and context.** For example:
   - If user rule says "Alert me if YouTube video is paused" → message: "The YouTube video is currently paused at 5:32"
   - If user rule says "Tell me when the video completes" → message: "The video has finished playing - it reached the end"
   - If user rule says "Notify me about tab changes" → message: "User switched from Gmail tab to YouTube tab"
   The message should feel like a direct answer to what the user asked to be monitored.
4. Do NOT fabricate rules. Do NOT generate alerts for things not in the USER RULES list.
5. If no USER RULES are listed, the alerts array must be empty [].
6. **When in doubt, TRIGGER the alert.** It is better to over-alert than to miss something the user asked to be notified about.

Return ONLY valid JSON:
{{
  "description": "Detailed description of the current screen — what apps are open, what content is visible, what the user appears to be doing. Include micro-state details.",
  "activity_type": "Primary activity (coding, browsing, communication, entertainment, productivity, etc.)",
  "detected_apps": ["App1", "App2"],
  "visible_items": ["Item1", "Item2"],
  "summary": "Detailed summary describing what the user is doing. Include specific states like 'video is paused', 'video is playing', 'typing a message', etc. If USER RULES request specific analysis, include that detailed answer here.",
  "change_importance": "low / medium / high",
  "user_notification": "A friendly one-line notification for the user, referencing what they're doing right now",
  "alerts": [
    {{
      "triggered": true,
      "rule_name": "Exact name from USER RULES list",
      "title": "Short, descriptive alert title",
      "message": "Alert message written in the context of the user's instruction — like a direct answer to what they asked to monitor",
      "severity": "info / warning / critical"
    }}
  ]
}}
"""

    start_time = time.time()

    try:

        # Use configured Gemini model from settings
        model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"

        print("settings.GEMINI_MODEL =", settings.GEMINI_MODEL)
        print("model_name =", model_name)
        

        model = genai.GenerativeModel(model_name)

        # pyrefly: ignore [parse-error]
        image_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode("utf-8")
        }

        # Retry loop for transient errors (429 rate limit, 503, etc.)
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = model.generate_content(
                    [prompt, image_part]
                )
                last_error = None
                break
            except Exception as retry_err:
                last_error = retry_err
                err_str = str(retry_err)
                # Retry on rate-limit (429) or server errors (5xx)
                if "429" in err_str or "503" in err_str or "500" in err_str:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}), retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise  # Non-retryable error, propagate immediately

        if last_error is not None:
            raise last_error

        processing_ms = int(
            (time.time() - start_time) * 1000
        )

        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "")
            raw_text = raw_text.replace("```", "")
            raw_text = raw_text.strip()

        result = json.loads(raw_text)

        result["processing_time_ms"] = processing_ms
        result["raw_response"] = response.text

        print("\nAI RESULT:")
        print(json.dumps(result, indent=2))

        return result

    except json.JSONDecodeError as e:

        return {
            "description": "Failed to parse AI response",
            "activity_type": "other",
            "detected_apps": [],
            "summary": "JSON parsing failed",
            "change_importance": "low",
            "alerts": [],
            "processing_time_ms": 0,
            "raw_response": str(e),
            "error": str(e)
        }

    except Exception as e:
        # Build a short, user-friendly summary from the error
        err_msg = str(e)
        if "429" in err_msg or "quota" in err_msg.lower():
            short_summary = "API quota exceeded — please check your Gemini billing"
        elif "401" in err_msg or "403" in err_msg:
            short_summary = "Invalid API key — please update GEMINI_API_KEY in .env"
        elif "404" in err_msg:
            short_summary = f"Model not found — check GEMINI_MODEL in .env"
        else:
            short_summary = f"AI error: {err_msg[:120]}"

        return {
            "description": f"AI service error: {err_msg}",
            "activity_type": "other",
            "detected_apps": [],
            "summary": short_summary,
            "change_importance": "low",
            "alerts": [],
            "processing_time_ms": 0,
            "raw_response": err_msg,
            "error": err_msg
        }