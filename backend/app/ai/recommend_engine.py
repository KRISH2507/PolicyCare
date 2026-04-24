import json
import logging
import re

import google.generativeai as genai

from app.core.config import settings
from app.services.vector_service import search_policy_chunks
from app.schemas.recommend import RecommendationRequest
from app.ai.prompts import RECOMMENDATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.1,
        response_mime_type="application/json",
    ),
    system_instruction=RECOMMENDATION_SYSTEM_PROMPT,
)


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


def generate_recommendation(profile: RecommendationRequest) -> dict:
    chunks = search_policy_chunks(query=build_query(profile), top_k=15)

    if not chunks:
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
        response = _model.generate_content(_build_context(profile, chunks))
        raw = re.sub(r"^```(?:json)?\s*", "", response.text.strip())
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Recommendation JSON parse failed: %s", e)
        raise ValueError(f"Gemini returned invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Gemini Recommendation Failed: {e}")
