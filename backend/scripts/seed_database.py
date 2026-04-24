"""
seed_database.py — AarogyaAid Database Training Script
=======================================================
Wipes and rebuilds ChromaDB with section-aware chunks.
Upserts 3 policy rows into PostgreSQL.

Run with:
    cd backend
    python seed_database.py
"""

import os
import sys
import time
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ─────────────────────────────────────────────
# Policy content
# ─────────────────────────────────────────────

POLICIES = [
    {
        "id": 1,
        "name": "CareShield Basic",
        "insurer": "NovaSure Health Insurance",
        "filename": "careshield_basic.txt",
        "content": """POLICY DOCUMENT — CareShield Basic
Insurer: NovaSure Health Insurance
Policy Name: CareShield Basic

OVERVIEW
CareShield Basic is an entry-level individual health insurance plan designed for young, healthy individuals in Tier-2 and Tier-3 cities with limited budgets.

PREMIUM
Annual Premium: Rs 5,000 per year
Coverage Amount: Rs 3,00,000 (3 Lakh)

ELIGIBILITY
Minimum Age: 18 years
Maximum Age: 45 years
Best suited for: Individuals under 35, sedentary or moderate lifestyle, no pre-existing conditions, annual income under Rs 3 Lakh, Tier-2 or Tier-3 cities

INCLUSIONS
- Inpatient hospitalisation (minimum 24 hours)
- Pre-hospitalisation expenses up to 30 days
- Post-hospitalisation expenses up to 60 days
- Ambulance charges up to Rs 2,000 per hospitalisation
- Day care procedures (listed 141 procedures)
- Government hospital cashless facility

EXCLUSIONS
- Pre-existing diseases and their complications for the first 4 years
- Diabetes and diabetes-related conditions for 4-year waiting period
- Hypertension and blood pressure conditions for 4-year waiting period
- Cardiac conditions for 4-year waiting period
- Asthma for 4-year waiting period
- Maternity and newborn expenses
- Cosmetic or plastic surgery
- Self-inflicted injuries
- Dental treatment (unless due to accident)
- OPD consultations and medicines

WAITING PERIODS
Initial waiting period: 30 days from policy start
Pre-existing disease waiting period: 4 years
Specific illness waiting period: 2 years

SUB-LIMITS
Room rent: Rs 1,000 per day (general ward)
ICU charges: Rs 2,000 per day
Doctor fees: Rs 500 per visit

CO-PAY
10% co-pay applicable for all claims
20% co-pay if treated in a non-network hospital

CLAIM TYPE
Cashless: Available at 2,000+ network hospitals
Reimbursement: Available for non-network hospitals

SUITABILITY
This plan is most suitable for young individuals aged 18-35 with no pre-existing conditions, living in Tier-2 or Tier-3 cities, earning under Rs 3 Lakh annually. Not recommended for anyone with diabetes, hypertension, cardiac conditions, or asthma due to the 4-year waiting period. The low premium makes it ideal for first-time insurance buyers on a tight budget.

NETWORK HOSPITALS
2,000+ hospitals across India, primarily in Tier-2 and Tier-3 cities""",
    },
    {
        "id": 2,
        "name": "MedProtect Plus",
        "insurer": "SecureLife Insurance",
        "filename": "medprotect_plus.txt",
        "content": """POLICY DOCUMENT — MedProtect Plus
Insurer: SecureLife Insurance
Policy Name: MedProtect Plus

OVERVIEW
MedProtect Plus is a mid-range individual and family health insurance plan designed for working professionals in metro and Tier-2 cities who may have pre-existing conditions like diabetes or hypertension.

PREMIUM
Annual Premium: Rs 12,000 per year (individual)
Coverage Amount: Rs 10,00,000 (10 Lakh)

ELIGIBILITY
Minimum Age: 18 years
Maximum Age: 65 years
Best suited for: Individuals aged 30-55, moderate lifestyle, pre-existing conditions like diabetes or hypertension, annual income Rs 3-15 Lakh, metro or Tier-2 cities

INCLUSIONS
- Inpatient hospitalisation (minimum 24 hours)
- Pre-hospitalisation expenses up to 60 days
- Post-hospitalisation expenses up to 90 days
- Ambulance charges up to Rs 5,000 per hospitalisation
- Day care procedures (all 540+ IRDAI listed procedures)
- Domiciliary hospitalisation
- AYUSH treatment coverage up to Rs 20,000
- Mental health hospitalisation covered
- Diabetes management and monitoring (after 2-year waiting period)
- Hypertension treatment (after 2-year waiting period)
- Organ donor expenses up to Rs 1,00,000
- Second medical opinion (online)

EXCLUSIONS
- Pre-existing diseases for first 2 years (reduced waiting period vs standard 4 years)
- Cosmetic surgery and aesthetic treatments
- Self-inflicted injuries and suicide attempts
- War and nuclear hazard related injuries
- Experimental treatments not approved by IRDAI
- Obesity treatment and weight loss surgery

WAITING PERIODS
Initial waiting period: 30 days from policy start
Pre-existing disease waiting period: 2 years (diabetes, hypertension, asthma, cardiac)
Specific illness waiting period: 1 year
Cancer and cardiac surgery: 90 days initial waiting period

SUB-LIMITS
Room rent: Rs 3,000 per day (single private room)
ICU charges: Rs 6,000 per day
No sub-limit on doctor or surgeon fees

CO-PAY
10% co-pay for Tier-2 city hospitals
No co-pay for metro city network hospitals
20% co-pay for non-network hospitals

CLAIM TYPE
Cashless: Available at 8,500+ network hospitals
Reimbursement: Available within 30 days of discharge

SUITABILITY
MedProtect Plus is best suited for individuals aged 30-55 who have or are at risk of diabetes, hypertension, or other lifestyle conditions. The 2-year waiting period (shorter than industry standard 4 years) for pre-existing conditions makes this plan particularly valuable for diabetic patients. The Rs 10 Lakh coverage is appropriate for metro and Tier-2 city residents where hospitalisation costs are higher. Recommended for income brackets Rs 3-15 Lakh annually.

NETWORK HOSPITALS
8,500+ hospitals across India, strong metro and Tier-2 coverage""",
    },
    {
        "id": 3,
        "name": "ActiveCover Premier",
        "insurer": "HealthFirst General Insurance",
        "filename": "activecover_premier.txt",
        "content": """POLICY DOCUMENT — ActiveCover Premier
Insurer: HealthFirst General Insurance
Policy Name: ActiveCover Premier

OVERVIEW
ActiveCover Premier is a comprehensive premium health insurance plan for active individuals and athletes in metro cities who want maximum coverage with OPD benefits and minimal waiting periods.

PREMIUM
Annual Premium: Rs 20,000 per year (individual)
Coverage Amount: Rs 25,00,000 (25 Lakh)

ELIGIBILITY
Minimum Age: 18 years
Maximum Age: 55 years
Best suited for: Individuals aged 25-50, active or athlete lifestyle, no or minimal pre-existing conditions, annual income Rs 8 Lakh and above, metro cities

INCLUSIONS
- Inpatient hospitalisation (minimum 24 hours)
- Pre-hospitalisation expenses up to 90 days
- Post-hospitalisation expenses up to 180 days
- OPD consultations covered up to Rs 15,000 per year
- Pharmacy and medicines (OPD) up to Rs 10,000 per year
- Diagnostic tests and lab work (OPD) up to Rs 8,000 per year
- Ambulance charges up to Rs 10,000 per hospitalisation
- Air ambulance up to Rs 2,50,000 per year
- All IRDAI listed day care procedures
- Sports injury and accident coverage (full)
- Physiotherapy up to Rs 20,000 per year
- Mental health OPD and IPD covered
- International emergency cover up to Rs 5,00,000
- Annual health check-up included (no sublimit)
- Maternity cover after 2 years (up to Rs 50,000)
- Newborn baby cover from day 1

EXCLUSIONS
- Pre-existing diseases for first 1 year only (shortest waiting period available)
- Cosmetic surgery unless required post-accident
- Self-inflicted injuries
- Intoxication-related hospitalisations

WAITING PERIODS
Initial waiting period: 15 days from policy start
Pre-existing disease waiting period: 1 year (shortest in market)
No waiting period for accidents and sports injuries

SUB-LIMITS
Room rent: No sub-limit (any room category covered)
ICU charges: No sub-limit
Doctor and surgeon fees: No sub-limit

CO-PAY
Zero co-pay for all network hospitals in metro cities
5% co-pay for Tier-2 city hospitals
15% co-pay for non-network hospitals

CLAIM TYPE
Cashless: Available at 12,000+ network hospitals nationwide
Reimbursement: Available within 15 days with digital claim filing
Dedicated claim relationship manager for all policyholders

SUITABILITY
ActiveCover Premier is designed for high-income, active individuals and athletes who want the best coverage available with minimal hassle. The OPD benefit makes it uniquely valuable for active people who require frequent physiotherapy, diagnostics, and consultations without hospitalisation. The 1-year pre-existing waiting period is the shortest available. Best suited for metro residents earning Rs 8 Lakh or above.

NETWORK HOSPITALS
12,000+ hospitals, highest concentration in metro cities (Delhi, Mumbai, Bangalore, Chennai, Hyderabad, Pune)""",
    },
]


# ─────────────────────────────────────────────
# Step 0 — Reset ChromaDB
# ─────────────────────────────────────────────

def reset_chroma(chroma_path: str):
    """Delete the existing 'policies' collection and create a fresh one."""
    import chromadb
    client = chromadb.PersistentClient(path=chroma_path)
    try:
        client.delete_collection("policies")
        print("  Existing Chroma collection deleted.")
    except Exception:
        print("  No existing collection to delete.")
    collection = client.get_or_create_collection(
        name="policies",
        metadata={"hnsw:space": "cosine"},
    )
    print(f"  Fresh collection created. Count: {collection.count()}")
    return collection


# ─────────────────────────────────────────────
# Step 1 — Write policy files
# ─────────────────────────────────────────────

def write_policy_files(sample_dir: str) -> dict:
    os.makedirs(sample_dir, exist_ok=True)
    paths = {}
    for p in POLICIES:
        filepath = os.path.join(sample_dir, p["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(p["content"])
        paths[p["id"]] = filepath
        print(f"  Written: {os.path.basename(filepath)}")
    return paths


# ─────────────────────────────────────────────
# Step 2 — Section-aware chunking
# ─────────────────────────────────────────────

def chunk_policy(policy: dict) -> list:
    """Use the section-aware chunker from chunk_service."""
    from app.services.chunk_service import chunk_by_section
    chunks = chunk_by_section(
        text=policy["content"],
        policy_name=policy["name"],
        insurer=policy["insurer"],
    )
    return chunks


# ─────────────────────────────────────────────
# Step 3 — Embed and store in ChromaDB
# ─────────────────────────────────────────────

def embed_and_store(policy: dict, chunks: list, collection) -> int:
    import google.generativeai as genai

    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    print(f"  Embedding {len(texts)} chunks...")

    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texts,
            task_type="retrieval_document",
        )
        embeddings = result["embedding"]
        if isinstance(embeddings[0], float):
            embeddings = [embeddings]
    except Exception as e:
        print(f"  ERROR embedding: {e}")
        raise

    ids = [f"policy_{policy['id']}_chunk_{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "policy_id": str(policy["id"]),
            "policy_name": policy["name"],
            "insurer": policy["insurer"],
            "source_file": policy["filename"],
            "section": c.get("section", "unknown"),
            "chunk_index": c["chunk_index"],
            "page_number": 1,
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=texts,
    )
    return len(chunks)


# ─────────────────────────────────────────────
# Step 4 — Upsert into PostgreSQL
# ─────────────────────────────────────────────

def upsert_policy_db(policy: dict, filepath: str, db_session):
    from sqlalchemy import text
    db_session.execute(
        text("""
            INSERT INTO policies (id, name, insurer, file_type, file_path, uploaded_at, uploaded_by, is_active)
            VALUES (:id, :name, :insurer, :file_type, :file_path, :uploaded_at, :uploaded_by, :is_active)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                insurer = EXCLUDED.insurer,
                file_path = EXCLUDED.file_path,
                uploaded_at = EXCLUDED.uploaded_at
        """),
        {
            "id": policy["id"],
            "name": policy["name"],
            "insurer": policy["insurer"],
            "file_type": "txt",
            "file_path": filepath,
            "uploaded_at": datetime.now(timezone.utc),
            "uploaded_by": "seed_script",
            "is_active": True,
        },
    )
    db_session.commit()


# ─────────────────────────────────────────────
# Step 5 — Verification
# ─────────────────────────────────────────────

def verify(collection):
    import google.generativeai as genai

    queries = [
        "diabetes coverage waiting period",
        "annual premium coverage amount",
        "OPD sports injury active lifestyle",
    ]

    for query in queries:
        print(f'\n  Query: "{query}"')
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=query,
            task_type="retrieval_query",
        )
        query_vec = result["embedding"]

        results = collection.query(
            query_embeddings=[query_vec],
            n_results=2,
            include=["documents", "metadatas", "distances"],
        )

        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            print(f"    [{meta['policy_name']} | {meta['section']}] dist={round(dist,3)}")
            # Show first line of chunk to confirm premium data is there
            first_line = doc.split("\n")[4] if len(doc.split("\n")) > 4 else doc[:80]
            print(f"    Preview: {first_line[:100]}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  AarogyaAid — Database Training & Seeding Script")
    print("  (Section-aware chunking + Gemini embeddings)")
    print("=" * 60 + "\n")

    import google.generativeai as genai
    from app.core.config import settings
    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Step 0: Reset Chroma
    print("STEP 0 — Resetting ChromaDB\n")
    collection = reset_chroma(settings.CHROMA_PATH)

    # Setup DB
    from app.core.database import SessionLocal, engine, Base
    import app.models
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Sample policies directory
    sample_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sample_policies"
    )

    # Step 1: Write files
    print("\nSTEP 1 — Writing policy files\n")
    file_paths = write_policy_files(sample_dir)

    # Steps 2-4: Chunk, embed, store
    print("\nSTEP 2-4 — Chunking, embedding, storing\n")
    chunk_counts = {}

    for policy in POLICIES:
        print(f"  [{policy['id']}] {policy['name']} ({policy['insurer']})")

        chunks = chunk_policy(policy)
        print(f"  Sections found: {len(chunks)}")
        for c in chunks:
            print(f"    - {c['section']}: {len(c['text'])} chars")

        n = embed_and_store(policy, chunks, collection)
        chunk_counts[policy["id"]] = n
        print(f"  Stored: {n} chunks in Chroma")

        upsert_policy_db(policy, file_paths[policy["id"]], db)
        print(f"  PostgreSQL: upserted\n")

        time.sleep(1)  # avoid embedding rate limit

    db.close()

    # Step 5: Verify
    print("STEP 5 — Verification queries\n")
    from sqlalchemy import text
    with engine.connect() as conn:
        row_count = conn.execute(text("SELECT COUNT(*) FROM policies")).scalar()

    verify(collection)

    # Summary
    print("\n" + "=" * 60)
    print("  === Seed complete ===")
    for p in POLICIES:
        print(f"  Policy {p['id']}: {p['name']} — {chunk_counts.get(p['id'], 0)} chunks")
    print(f"  Total chunks in Chroma : {collection.count()}")
    print(f"  PostgreSQL rows        : {row_count}")
    print("=" * 60)
    print()
    print("  Restart the server, then test:")
    print("  1. Go to http://localhost:5173")
    print("  2. Log in and fill the profile form")
    print("  3. You should see real premium values (e.g. Rs 12,000)")
    print("  4. Chat should answer specific questions from the document")
    print()


if __name__ == "__main__":
    main()
