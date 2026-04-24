import json
from openai import OpenAI
from app.core.config import settings
from app.services.vector_service import search_policy_chunks
from app.schemas.recommend import RecommendationRequest
from app.ai.prompts import RECOMMENDATION_SYSTEM_PROMPT

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_query_from_profile(profile: RecommendationRequest) -> str:
    """Converts the user profile into an optimized fuzzy search query."""
    conditions = " ".join(profile.pre_existing_conditions) if profile.pre_existing_conditions else "healthy no pre-existing conditions"
    
    query = (
        f"health insurance policy details for {profile.age} year old in {profile.city_tier} city with "
        f"{conditions} conditions, {profile.lifestyle} lifestyle, income {profile.income_band}."
    )
    
    # Priority logic appending for vector weighting
    if profile.pre_existing_conditions:
         query += " focus on waiting periods for pre-existing diseases."
    if profile.income_band in ["under 3L", "3-8L"]:
         query += " focus on affordability, low premiums, and value coverage."
    if profile.lifestyle in ["Active", "Athlete"]:
         query += " focus on OPD, sports injuries, and wellness benefits."
         
    return query

def generate_recommendation(profile: RecommendationRequest) -> dict:
    
    # 1. Convert user profile into retrieval query
    query = generate_query_from_profile(profile)
    
    # 2. Retrieve chunks across previously uploaded admin policies
    retrieved_chunks = search_policy_chunks(query=query, top_k=10)
    
    # Graceful fallback if ChromaDB is barren
    if not retrieved_chunks:
        return {
            "best_fit": None,
            "peer_comparison": [],
            "coverage_detail": None,
            "why_this_policy": (
                f"Hello {profile.full_name}, I understand you are living in a {profile.city_tier} area with "
                f"a {profile.lifestyle.lower()} lifestyle. Unfortunately, our current database does not contain "
                f"policies matching your specific needs. Please check back after your admin adds more plans!"
            ),
            "citations": []
        }

    # 3. Group chunks by policy and Format explicit real context strings enforcing AI grounding
    # Grouping logic groups multiple chunks related to the same policy gracefully
    grouped_policies = {}
    for chunk in retrieved_chunks:
        meta = chunk["metadata"]
        policy_slug = f"{meta.get('policy_name', 'Unknown')} ({meta.get('insurer', 'Unknown')})"
        
        if policy_slug not in grouped_policies:
            grouped_policies[policy_slug] = []
        
        doc_text = chunk["document"]
        page_num = meta.get('page_number', '?')
        grouped_policies[policy_slug].append(f"[Page {page_num}]: {doc_text}")

    context_text = "RETRIEVED POLICY DOCUMENTS:\n\n"
    for policy, blocks in grouped_policies.items():
        context_text += f"--- Policy: {policy} ---\n"
        for b in blocks:
            context_text += f"{b}\n"
        context_text += "\n"

    user_prompt = f"""
USER PROFILE:
Full Name: {profile.full_name}
Age: {profile.age}
City Tier: {profile.city_tier}
Lifestyle: {profile.lifestyle}
Pre-existing Conditions: {', '.join(profile.pre_existing_conditions) if profile.pre_existing_conditions else 'None'}
Income Band: {profile.income_band}

Based on the rules and retrieved documents provided above, please return the JSON recommendation evaluating which policy is the best match.
"""
    
    # 4. Call OpenAI API explicitly forcing structural schema
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                {"role": "system", "content": context_text},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2
        )
        
        # 5. Parse out safely
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)
        
    except Exception as e:
        raise ValueError(f"OpenAI Generation Failed: {str(e)}")