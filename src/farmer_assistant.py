import os
from dotenv import load_dotenv
import groq
from groq import (
    Groq,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    APIStatusError,
    GroqError
)

# Robustly find and load .env from project backend root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    load_dotenv(override=True)

# Configurable Groq model with currently supported defaults
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
FALLBACK_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]

def validate_groq_api_key():
    """Startup verification of GROQ_API_KEY with user-friendly warnings."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        print("\n" + "=" * 70)
        print("[WARNING] [Groq Setup] GROQ_API_KEY is missing or empty!")
        print("The Smart Farm Advisor chatbot requires a valid Groq API key.")
        print(f"Please configure your key in: {ENV_FILE}")
        print("Example: GROQ_API_KEY=gsk_your_groq_api_key_here")
        print("=" * 70 + "\n")
        return False
    masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    print(f"[OK] [Groq Setup] GROQ_API_KEY loaded ({masked}) | Primary Model: {PRIMARY_MODEL}")
    return True

validate_groq_api_key()


SYSTEM_PROMPT = """
You are Smart Farm Advisor, a friendly, intelligent and natural conversational AI assistant.

Your job is to understand what the user actually wants and respond naturally.

IMPORTANT:
You are NOT only a farming chatbot.
You can have normal conversations and answer general questions too.

==================================================
1. GENERAL CONVERSATION
==================================================

You can handle:

- Greetings
- Small talk
- General questions
- General knowledge
- Jokes
- Fun conversations
- Motivation
- Study-related questions
- Technology questions
- Casual conversations
- Farming and agriculture questions
- Plant disease questions
- Questions about the user's scan result
- Follow-up questions

Examples:

User: Hi
Assistant: Hey! 😊 How are you?

User: I'm good
Assistant: That's nice to hear! What are you up to?

User: I'm bored
Assistant: Haha 😄 Let's change that. What do you feel like doing?

User: Tell me a joke
Assistant: Sure 😄 Why did the tomato turn red? Because it saw the salad dressing!

DO NOT mention farming when the user is talking about an unrelated topic.

==================================================
2. UNDERSTAND THE USER FIRST
==================================================

Before answering:

1. Understand the user's message.
2. Check the previous conversation.
3. Identify what the user is actually asking.
4. Answer that question directly.
5. Use previous information when it is relevant.
6. Do not make assumptions.

If the user changes the topic, follow the new topic.

If the user asks a follow-up question such as:

- "what about that?"
- "and this one?"
- "why?"
- "how?"
- "what should I do?"
- "what about older leaves?"

Use the previous conversation to understand what they mean.

Do NOT ask the user to repeat information that is already available in the conversation.

==================================================
3. FARMING MODE
==================================================

When the user asks about farming, agriculture, crops or plant diseases:

Give practical and easy-to-understand advice.

For plant disease questions, when appropriate explain:

- Possible cause
- Symptoms
- Organic remedy
- Chemical/control option
- Prevention

Do not give unnecessarily complicated explanations.

==================================================
4. SCAN INFORMATION
==================================================

A crop scan may sometimes be provided.

Current scan information:

{active_scan}

IMPORTANT:

Use scan information ONLY when it is relevant to the user's question.

If there is no scan information, do NOT invent one.

Never tell the user that they have a disease just because scan information exists.

If the user asks about the scan, explain the scan result clearly.

==================================================
5. NATURAL CONVERSATION
==================================================

Be friendly, warm and conversational.

Do not sound like a robot.

Do not start every answer with:

"As a Smart Farm Advisor..."

Do not repeat the same sentence patterns.

Do not unnecessarily repeat information.

Use 0-2 emojis when appropriate.

==================================================
6. LANGUAGE
==================================================

Understand the language used by the user.

Respond in the same language whenever possible.

Support:

- English
- Kannada
- Hindi
- Tanglish
- Kanglish
- Mixed languages

If the user changes language, naturally change with them.

==================================================
7. IMPORTANT
==================================================

Never say:

"I can only answer farming questions."

Never reject a normal question just because it is unrelated to farming.

If you know the answer, answer it naturally.

If you are unsure, honestly say so and provide the useful information you do know.

MOST IMPORTANT RULE:

Understand first.
Respond second.

You are a natural conversational AI assistant with strong farming expertise.
"""


def get_farming_response(
    user_message,
    chat_history=None,
    active_scan=None,
    lang="en"
):
    """
    Generate an AI response using Groq.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        print("\n[Groq Error] Missing GROQ_API_KEY: GROQ_API_KEY environment variable is not set or empty in .env.")
        return "API key missing: Please set your GROQ_API_KEY in the .env file."

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"\n[Groq Error] Groq client initialization error: {e}")
        return f"Groq client error: {e}"

    # --------------------------------------------------
    # Scan context
    # --------------------------------------------------
    if active_scan:
        scan_context = active_scan
    else:
        scan_context = "No crop scan is currently available."

    # --------------------------------------------------
    # System message
    # --------------------------------------------------
    system_message = SYSTEM_PROMPT.format(
        active_scan=scan_context
    )

    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]

    # --------------------------------------------------
    # Add conversation history
    # --------------------------------------------------
    if chat_history:
        for msg in chat_history[-12:]:
            # Make sure message is a dictionary
            if not isinstance(msg, dict):
                continue

            role = msg.get("role")
            content = msg.get("content")

            # Only accept valid chat roles
            if role not in ["user", "assistant"]:
                continue

            if not content:
                continue

            messages.append(
                {
                    "role": role,
                    "content": str(content)
                }
            )

    # --------------------------------------------------
    # Add current user message
    # --------------------------------------------------
    messages.append(
        {
            "role": "user",
            "content": str(user_message)
        }
    )

    # --------------------------------------------------
    # Ask Groq (try configured primary model with fallbacks)
    # --------------------------------------------------
    active_primary = os.getenv("GROQ_MODEL", PRIMARY_MODEL).strip()
    candidate_models = [active_primary] + [m for m in FALLBACK_MODELS if m != active_primary]
    last_error_detail = None

    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=700
            )

            answer = response.choices[0].message.content
            if not answer:
                return "Sorry, I couldn't generate a response."

            return answer.strip()

        except AuthenticationError as e:
            # 401 Unauthorized - invalid key
            print(f"\n[Groq Error] Invalid GROQ_API_KEY (401 Authentication Error): {e}")
            return "Invalid API key: Authentication failed. Please check that your GROQ_API_KEY in .env is valid."

        except RateLimitError as e:
            # 429 Rate Limit
            print(f"\n[Groq Error] Rate limit reached (429 Rate Limit Error): {e}")
            return "Rate limit exceeded: The AI service is currently receiving too many requests. Please wait a moment and try again."

        except (APIConnectionError, APITimeoutError) as e:
            # Network or timeout error
            print(f"\n[Groq Error] Network/Connection error: {e}")
            return "Network error: Unable to connect to Groq AI servers. Please check your internet connection."

        except NotFoundError as e:
            # 404 Model not found - try fallback
            print(f"\n[Groq Warning] Model not found on Groq: '{model_name}' (404). Trying fallback model...")
            last_error_detail = f"Model not found: '{model_name}' does not exist or you do not have access to it on Groq."
            continue

        except BadRequestError as e:
            # 400 Bad request / decommissioned model
            print(f"\n[Groq Warning] Bad request error with model '{model_name}': {e}")
            if "decommissioned" in str(e).lower():
                last_error_detail = f"Model decommissioned: '{model_name}' has been decommissioned by Groq. Please use a supported model like qwen/qwen3.8-27b or openai/gpt-oss-20b."
            else:
                last_error_detail = f"Bad request error: {e}"
            continue

        except APIStatusError as e:
            print(f"\n[Groq Error] Groq API status error ({e.status_code}): {e}")
            return f"API status error ({e.status_code}): {e.message if hasattr(e, 'message') else str(e)}"

        except GroqError as e:
            print(f"\n[Groq Error] Groq API error: {e}")
            return f"Groq API error: {e}"

        except Exception as e:
            print(f"\n[Groq Error] Unexpected error calling Groq: {type(e).__name__}: {e}")
            return f"AI service error: {e}"

    if last_error_detail:
        print(f"\n[Groq Error] All attempted models failed. {last_error_detail}")
        return last_error_detail

    return "AI service error: Unable to generate a response from Groq."


# ======================================================
# FARMER ASSISTANT CLASS
# ======================================================

class FarmerAssistant:

    def __init__(self):
        # Stores conversations separately for each session
        self._sessions = {}

    # --------------------------------------------------
    # Get or create session
    # --------------------------------------------------

    def get_context(self, session_id):

        if session_id is None:
            session_id = "default"

        if session_id not in self._sessions:

            self._sessions[session_id] = {
                "lang": "en",
                "history": [],
                "active_scan": None
            }

        return self._sessions[session_id]

    # --------------------------------------------------
    # Clear conversation
    # --------------------------------------------------

    def clear_context(self, session_id):

        if session_id in self._sessions:
            del self._sessions[session_id]

    # --------------------------------------------------
    # Handle user message
    # --------------------------------------------------

    def handle_message(
        self,
        query,
        lang="en",
        session_id=None,
        last_prediction=None,
        chat_history=None,
        active_scan=None
    ):

        # Use default session if no ID is provided
        if session_id is None:
            session_id = "default"

        # Get session
        context = self.get_context(session_id)

        # --------------------------------------------------
        # Language
        # --------------------------------------------------

        if lang:
            context["lang"] = lang

        # --------------------------------------------------
        # Conversation history
        # --------------------------------------------------

        if chat_history is not None:

            # Use history supplied by the application
            context["history"] = list(chat_history)

        history = context["history"]

        # --------------------------------------------------
        # Crop scan information
        # --------------------------------------------------

        if active_scan:
            context["active_scan"] = active_scan

        elif last_prediction:

            label = last_prediction.get("label", "")

            label = (
                label
                .replace("___", " - ")
                .replace("_", " ")
            )

            try:
                confidence = float(
                    last_prediction.get("confidence", 0.0)
                ) * 100

                context["active_scan"] = (
                    f"{label} ({confidence:.0f}%)"
                )

            except (ValueError, TypeError):

                context["active_scan"] = label

        # IMPORTANT:
        # Do NOT create a fake scan result.
        #
        # Old code had:
        # "Tomato - Late blight 43%"
        #
        # That caused unrelated conversations
        # to receive fake tomato disease context.

        current_scan = context.get("active_scan")

        # --------------------------------------------------
        # Generate AI response
        # --------------------------------------------------

        answer = get_farming_response(
            user_message=query,
            chat_history=history,
            active_scan=current_scan,
            lang=context["lang"]
        )

        # --------------------------------------------------
        # Save conversation
        # --------------------------------------------------

        history.append(
            {
                "role": "user",
                "content": str(query)
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": str(answer)
            }
        )

        # Keep memory manageable
        context["history"] = history[-20:]

        return answer


# ======================================================
# GLOBAL INSTANCE
# ======================================================

farmer_assistant = FarmerAssistant()


__all__ = [
    "SYSTEM_PROMPT",
    "get_farming_response",
    "FarmerAssistant",
    "farmer_assistant"
]