# AarogyaAid — Product Requirements Document

**Version:** 1.0  
**Date:** April 2026  
**Author:** Engineering Team

---

## User Persona

**Priya, 34, Bengaluru**

Priya is a mid-level software professional earning ₹7 lakh a year. She was diagnosed with Type 2 diabetes two years ago and knows she needs health insurance — but every time she tries to research it, she ends up more confused than when she started. She has spent hours on comparison websites that show her 40 plans with no explanation of which one actually covers diabetes. She has called two insurance agents who gave her conflicting information and pushed expensive plans she couldn't afford. She doesn't know what "co-pay", "sub-limit", or "PED waiting period" mean in practice. She wants someone to just tell her: *which plan is right for me, and why?*

---

## Core Pain Points

1. **Information overload** — Comparison sites show dozens of plans with no personalisation. Priya can't tell which ones actually cover her condition.

2. **Jargon barrier** — Terms like "co-pay", "sub-limit", "waiting period", and "cashless network" are not explained in plain language anywhere in the purchase flow.

3. **Trust deficit** — Agents have a financial incentive to push expensive plans. Priya doesn't trust recommendations that aren't grounded in the actual policy document.

4. **No follow-up channel** — After getting a recommendation, there is no way to ask "but what happens if I need dialysis?" without calling an agent again.

5. **Pre-existing condition anxiety** — Priya specifically needs to know how her diabetes is treated under each plan. Generic comparison tables don't surface this clearly.

---

## Product Goals

1. Reduce the time from "I need insurance" to "I understand my best option" from hours to under 5 minutes.
2. Ground every recommendation in the actual text of uploaded policy documents — no hallucinated coverage details.
3. Let users ask follow-up questions in plain language and get answers that cite the source document.
4. Give admins a simple interface to keep the policy knowledge base current without engineering involvement.

---

## Feature Prioritisation

Features were prioritised using a simple impact vs. effort framework. The most critical user need — getting a trustworthy, personalised recommendation — was built first.

| Priority | Feature | Rationale |
|---|---|---|
| P0 | 6-field profile form + recommendation engine | Core product value. Nothing else matters if this doesn't work. |
| P0 | RAG pipeline (upload → embed → retrieve → generate) | Grounding is what separates this from a generic chatbot. |
| P0 | Admin upload interface | Without policies in the database, the engine has nothing to recommend. |
| P1 | Explainer chat panel | Addresses the follow-up question pain point. High value, moderate effort. |
| P1 | JWT auth + role separation | Required for admin security. Low effort given FastAPI's dependency injection. |
| P2 | Peer comparison table | Useful context but not the primary decision driver. |
| P2 | Coverage breakdown (inclusions/exclusions) | Adds depth to the recommendation. |
| P3 | Landing page + signup flow | Needed for a complete product feel but not core to the AI functionality. |

---

## Matching Logic by Profile Field

The recommendation engine converts the user's profile into a semantic search query that retrieves the most relevant policy document chunks from ChromaDB. GPT-4o-mini then reasons over those chunks to produce a structured recommendation.

| Field | Values | Matching influence |
|---|---|---|
| `age` | Integer (1–99) | Included in retrieval query. LLM uses it to assess premium bands, entry age eligibility, and age-based co-pay clauses. |
| `city_tier` | metro / tier2 / tier3 | Metro users need higher room rent limits and broader cashless networks. Query is weighted toward these attributes for metro users. |
| `lifestyle` | sedentary / moderate / active / athlete | Active and athlete profiles append OPD, sports injury, and wellness benefit keywords. Sedentary profiles focus on hospitalisation cover. |
| `pre_existing_conditions` | List (diabetes, hypertension, asthma, cardiac, none, other) | Appends "waiting period for pre-existing diseases" to the query. LLM is instructed to prioritise plans with shorter PED waiting periods and to explicitly state the waiting period for the user's specific condition. |
| `income_band` | under3l / 3to8l / 8to15l / above15l | Low-income bands append affordability and low-premium keywords. High-income bands allow premium plans with OPD and wellness benefits to surface. |
| `full_name` | String | Used in the personalised `why_this_policy` explanation to make the response feel addressed to the individual. |

---

## Assumptions

- The admin uploads policy documents that are accurate and current. The AI cannot verify policy terms against external sources.
- Users provide honest health information. The system does not validate medical claims.
- The OpenAI API is available and the API key has sufficient quota for embeddings and completions.
- The product is used in a local or trusted network environment. Production deployment would require HTTPS, rate limiting, and a managed database.
- "Admin" is a single trusted operator role. Multi-admin support with audit logs is a future scope item.

---

## Success Metrics

| Metric | Target | How to measure |
|---|---|---|
| Time to recommendation | < 2 minutes from profile submission | Frontend timing from form submit to results render |
| Recommendation grounding rate | 100% of responses cite at least one source document | Check `citations` array in API response |
| Chat answer relevance | User does not need to ask the same question twice | Qualitative review of chat sessions |
| Admin upload success rate | > 95% of valid documents vectorised without error | Backend error logs |
| Test coverage | All core engine logic covered by unit tests | `pytest --cov` report |

---

## Future Scope

- **Hindi and regional language support** — extend the system prompt to respond in the user's preferred language.
- **Government scheme integration** — automatically index Ayushman Bharat, PMJAY, and state-level scheme documents.
- **Premium calculator** — show estimated annual premium based on age and cover amount.
- **Policy renewal reminders** — notify users when their recommended policy is due for renewal.
- **Agent comparison mode** — let users compare two policies side by side with a structured diff view.
- **Feedback and re-ranking** — collect thumbs up/down on recommendations to improve retrieval quality over time.
- **Multi-user admin** — role-based access control with audit logs for enterprise deployments.
