import json
import logging
import re
import traceback

import google.generativeai as genai

from app.core.config import settings
from app.services.vector_service import search_policy_chunks
from app.schemas.recommend import RecommendationRequest
from app.ai.prompts import RECOMMENDATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.1,
        response_mime_type="application/json",
    ),
    system_instruction=RECOMMENDATION_SYSTEM_PROMPT,
)

_FALLBACK_RESPONSE = {
    "best_fit": None,
    "peer_comparison": [],
    "coverage_detail": None,
    "why_this_policy": (
        "Unable to generate a personalized recommendation right now. "
        "Your profile has been saved. Please try again in a moment."
    ),
    "citations": [],
}


def build_query(profile: RecommendationRequest) -> str:
    conditions = ", ".join(profile.pre_existing_conditions) if profile.pre_existing_conditions else "none"
    return (
        f"health insurance policy premium coverage amount inclusions exclusions "
        f"waiting period for {conditions} "
        f"income {profile.income_band} city {profile.city_tier} "
        f"lifestyle {profile.lifestyle} age {profile.age}"
    )


# alias kept for tests
generate_query_from_profile = build_query


def _build_context(profile: RecommendationRequest, chunks: list) -> str:
    chunk_text = ""
    for i, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        section = meta.get("section", meta.get("page_number", "unknown"))
        chunk_text += (
            f"\n\n--- CHUNK {i+1} "
            f"| Policy: {meta.get('policy_name', 'Unknown')} "
            f"| Insurer: {meta.get('insurer', 'Unknown')} "
            f"| Section: {section} ---\n"
            f"{chunk['document']}"
        )

    conditions_str = ", ".join(profile.pre_existing_conditions) if profile.pre_existing_conditions else "None"

    return (
        f"USER PROFILE:\n"
        f"Name: {profile.full_name}\n"
        f"Age: {profile.age}\n"
        f"City Tier: {profile.city_tier}\n"
        f"Lifestyle: {profile.lifestyle}\n"
        f"Pre-existing Conditions: {conditions_str}\n"
        f"Annual Income Band: {profile.income_band}\n\n"
        f"RETRIEVED POLICY CHUNKS:\n{chunk_text}\n\n"
        f"Return the recommendation JSON. Extract premium and coverage amounts from "
        f"lines starting with 'Annual Premium:' and 'Coverage Amount:' in the PREMIUM chunks."
    )


def _parse_gemini_response(response) -> dict:
    """Safely extract and parse JSON from a Gemini response object."""
    # Check for blocked / empty response
    if not response or not response.candidates:
        logger.warning("[recommend] Gemini response has no candidates — using fallback.")
        return None

    candidate = response.candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)
    # finish_reason 3 == SAFETY block in the Gemini SDK
    if finish_reason == 3:
        logger.warning("[recommend] Gemini response blocked by safety filter — using fallback.")
        return None

    raw_text = None
    try:
        raw_text = response.text
    except Exception:
        logger.warning("[recommend] response.text raised — using fallback.")
        return None

    if not raw_text or not raw_text.strip():
        logger.warning("[recommend] Gemini returned empty text — using fallback.")
        return None

    # Strip markdown code fences if present
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        logger.info("[recommend] Gemini JSON parsed successfully.")
        return parsed
    except json.JSONDecodeError as e:
        logger.error("[recommend] JSON parse failed: %s | raw snippet: %.300s", e, cleaned)
        return None


def generate_recommendation(profile: RecommendationRequest) -> dict:
    logger.info("[recommend] Request started for user: %s", profile.full_name)

    chunks = search_policy_chunks(query=build_query(profile), top_k=15)
    logger.info("[recommend] Vector search complete — %d chunks retrieved.", len(chunks) if chunks else 0)

    if not chunks:
        logger.warning("[recommend] No chunks found in vector store — returning empty policy fallback.")
        return {
            "best_fit": None,
            "peer_comparison": [],
            "coverage_detail": None,
            "why_this_policy": (
                f"Hello {profile.full_name}, unfortunately our database does not contain "
                f"policies matching your needs yet. Please ask an admin to upload policy documents."
            ),
            "citations": [],
        }

    try:
        context = _build_context(profile, chunks)
        response = _model.generate_content(context)
        logger.info("[recommend] Gemini response received.")

        parsed = _parse_gemini_response(response)
        if parsed is None:
            logger.warning("[recommend] Falling back to fallback response due to unparseable Gemini output.")
            return _FALLBACK_RESPONSE

        return parsed

    except Exception as e:
        logger.error("[recommend] Gemini call failed: %s\n%s", e, traceback.format_exc())
        logger.warning("[recommend] Using fallback response.")
        return _FALLBACK_RESPONSE
