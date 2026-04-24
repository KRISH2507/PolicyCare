import json
from openai import OpenAI
from app.core.config import settings
from app.services.vector_service import search_policy_chunks
from app.schemas.chat import ChatRequest

# Initialize persistent OpenAI Text Embedding client 
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

CHAT_SYSTEM_PROMPT = """You are AarogyaAid, an empathetic Indian health insurance advisor answering follow-up questions about a recommended policy.

CRITICAL RULES:
1. SAFE SCOPE: NEVER diagnose symptoms, prescribe medicine, or recommend surgeries. If a user asks "Should I get surgery?" or "Diagnose my symptoms", politely decline and redirect to insurance coverage limits and procedures.
2. TONE: Be warm, respectful, and use plain English. Define jargon (like co-pay, waiting period, sub-limits) the first time you use it.
3. GROUNDING & HALLUCINATION: Only use the retrieved policy documents provided. If the information is missing from the uploaded documents, explicitly state: "This information is unavailable in the uploaded documents."
4. LENGTH: Keep answers concise (max ~180 words) unless a detailed comparison is requested.
5. CONTEXT: Read the user's profile and chat history to provide personalized, realistic examples based on their condition, lifestyle, and city tier. Do not ask for profile fields you already have.
6. CITATIONS: Always cite the actual filename and page number when quoting factual policy details.

Output strictly as a JSON object:
{
  "reply": "Your conversational answer here...",
  "citations": ["Document Name (Page X)"],
  "requires_followup": true/false
}
"""

def generate_chat_reply(request: ChatRequest) -> dict:
    
    profile = request.user_profile
    conditions_list = profile.get("pre_existing_conditions", [])
    conditions_str = " ".join(conditions_list) if conditions_list else "healthy"
    
    # B. Build a hyper-focused retrieval query weighing their actual profile context
    search_query = (
        f"{request.message} {request.recommended_policy_name} "
        f"{profile.get('city_tier', '')} {conditions_str}"
    )
    
    # C. Search Chroma, strictly filtering to the recommended policy if provided
    policy_ids = [request.recommended_policy_id] if request.recommended_policy_id else None
    retrieved_chunks = search_policy_chunks(query=search_query, top_k=7, policy_ids=policy_ids)
    
    # Build context block
    context_text = "RETRIEVED POLICY DOCUMENTS:\n\n"
    if not retrieved_chunks:
        context_text += "No relevant documents found in the database. Rely strictly on graceful fallbacks.\n"
    else:
        for i, chunk in enumerate(retrieved_chunks):
            meta = chunk["metadata"]
            doc_text = chunk["document"]
            context_text += f"---\nPolicy: {meta.get('policy_name', 'Unknown')} | Insurer: {meta.get('insurer', 'Unknown')} | Page: {meta.get('page_number', '?')}\nContent: {doc_text}\n"

    # Provide Profile explicitly to the LLM memory block
    profile_text = (
        f"USER PROFILE:\n{json.dumps(profile, indent=2)}\n\n"
        f"RECOMMENDED POLICY CONTEXT: {request.recommended_policy_name}"
    )

    # Initialize Chat History
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "system", "content": profile_text},
        {"role": "system", "content": context_text}
    ]
    
    # D. Inject Previous Chat History dynamically
    for msg in request.history[-6:]:  # Keep context window efficient (last 6 interactions)
        role = msg.get("role")
        if role in ["user", "assistant"]:
            messages.append({"role": role, "content": msg.get("content", "")})
            
    # Inject current message payload
    messages.append({"role": "user", "content": request.message})
    
    # E. Call OpenAI API explicitly forcing structural schema
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)
        
    except Exception as e:
        raise ValueError(f"OpenAI Chat Generation Failed: {str(e)}")