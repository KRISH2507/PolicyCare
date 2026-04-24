import json
import logging
import re

import google.generativeai as genai

from app.core.config import settings
from app.services.vector_service import search_policy_chunks
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

_SYSTEM_PROMPT = """You are a health insurance explainer for AarogyaAid. You help users understand their recommended health insurance policy.

You will receive:
1. The user's profile (name, age, conditions, city, lifestyle, income)
2. The recommended policy name
3. POLICY CONTEXT: retrieved chunks from the actual policy document
4. The conversation history

RULES:
- Answer ONLY from the POLICY CONTEXT. If the answer is there, give it clearly. Never say "no information available" if the context contains relevant text.
- For premium or coverage questions, look for lines starting with "Annual Premium:" and "Coverage Amount:" in the context.
- End every factual answer with: "— Source: [policy_name, section]"
- If the context genuinely lacks the answer: "The policy document doesn't cover that detail. Contact the insurer directly."
- For medical questions: "I can only help with insurance coverage questions — I'm not able to give medical advice."
- Use the user's name in your first response. Never ask for profile fields you already have.
- When explaining jargon, define it plainly first, then apply it to the user's situation.
- Plain conversational text only. No markdown.

Output as JSON:
{
  "reply": "...",
  "citations": ["Policy Name — Section Name"],
  "requires_followup": true/false
}"""

_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.2,
        response_mime_type="application/json",
    ),
    system_instruction=_SYSTEM_PROMPT,
)


def generate_chat_reply(request: ChatRequest) -> dict:
    profile = request.user_profile
    conditions_str = " ".join(profile.get("pre_existing_conditions", [])) or "healthy"

    search_query = (
        f"{request.message} policy premium coverage waiting period "
        f"inclusions exclusions {request.recommended_policy_name} "
        f"{conditions_str} {profile.get('city_tier', '')}"
    )

    policy_ids = [request.recommended_policy_id] if request.recommended_policy_id else None
    chunks = search_policy_chunks(query=search_query, top_k=8, policy_ids=policy_ids)

    if not chunks:
        context_block = "POLICY CONTEXT:\nNo relevant chunks found.\n"
    else:
        context_block = "POLICY CONTEXT:\n"
        for i, chunk in enumerate(chunks):
            meta = chunk["metadata"]
            section = meta.get("section", f"Page {meta.get('page_number', '?')}")
            context_block += (
                f"\n--- CHUNK {i+1} | Policy: {meta.get('policy_name')} "
                f"| Section: {section} ---\n{chunk['document']}\n"
            )

    history_text = ""
    for msg in request.history[-6:]:
        role = msg.get("role", "")
        if role in ("user", "assistant"):
            history_text += f"{role.capitalize()}: {msg.get('content', '')}\n"

    prompt = (
        f"USER PROFILE:\n{json.dumps(profile, indent=2)}\n\n"
        f"RECOMMENDED POLICY: {request.recommended_policy_name}\n\n"
        f"{context_block}\n"
        f"CONVERSATION HISTORY:\n{history_text}\n"
        f"User: {request.message}"
    )

    try:
        response = _model.generate_content(prompt)
        raw = re.sub(r"^```(?:json)?\s*", "", response.text.strip())
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Chat JSON parse failed: %s", e)
        raise ValueError(f"Gemini Chat returned invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Gemini Chat Failed: {e}")
