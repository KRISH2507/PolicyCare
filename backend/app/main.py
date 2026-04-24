import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.routes import auth, recommend, chat, admin
import app.models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Policy content bundled directly — no external files needed ──
SEED_POLICIES = [
    {
        "id": 1, "name": "CareShield Basic", "insurer": "NovaSure Health Insurance",
        "content": """POLICY DOCUMENT — CareShield Basic
Insurer: NovaSure Health Insurance
Policy Name: CareShield Basic

OVERVIEW
CareShield Basic is an entry-level individual health insurance plan for young, healthy individuals in Tier-2 and Tier-3 cities with limited budgets.

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
- Day care procedures (141 listed procedures)
- Government hospital cashless facility

EXCLUSIONS
- Pre-existing diseases for the first 4 years
- Diabetes and diabetes-related conditions: 4-year waiting period
- Hypertension and blood pressure conditions: 4-year waiting period
- Cardiac conditions: 4-year waiting period
- Asthma: 4-year waiting period
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
Best for young individuals aged 18-35 with no pre-existing conditions in Tier-2 or Tier-3 cities earning under Rs 3 Lakh. Not recommended for anyone with diabetes, hypertension, cardiac conditions, or asthma due to the 4-year waiting period.

NETWORK HOSPITALS
2,000+ hospitals across India, primarily in Tier-2 and Tier-3 cities""",
    },
    {
        "id": 2, "name": "MedProtect Plus", "insurer": "SecureLife Insurance",
        "content": """POLICY DOCUMENT — MedProtect Plus
Insurer: SecureLife Insurance
Policy Name: MedProtect Plus

OVERVIEW
MedProtect Plus is a mid-range health insurance plan for working professionals in metro and Tier-2 cities who may have pre-existing conditions like diabetes or hypertension.

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
- Pre-existing diseases for first 2 years (shorter than standard 4 years)
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
Best for individuals aged 30-55 with diabetes, hypertension, or other lifestyle conditions. The 2-year waiting period (shorter than industry standard 4 years) makes this plan valuable for diabetic patients. Rs 10 Lakh coverage suits metro and Tier-2 city residents. Recommended for income Rs 3-15 Lakh annually.

NETWORK HOSPITALS
8,500+ hospitals across India, strong metro and Tier-2 coverage""",
    },
    {
        "id": 3, "name": "ActiveCover Premier", "insurer": "HealthFirst General Insurance",
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
Best for high-income active individuals and athletes wanting maximum coverage with minimal hassle. OPD benefit is uniquely valuable for frequent physiotherapy and diagnostics. The 1-year pre-existing waiting period is the shortest available. Best for metro residents earning Rs 8 Lakh or above.

NETWORK HOSPITALS
12,000+ hospitals, highest concentration in metro cities (Delhi, Mumbai, Bangalore, Chennai, Hyderabad, Pune)""",
    },
]


def _auto_seed():
    """Seed the vector store and DB on first startup if empty."""
    from app.services.vector_service import collection, embed_texts
    from app.services.chunk_service import chunk_by_section
    from sqlalchemy import text

    if collection.count() > 0:
        logger.info("Vector store already seeded (%d chunks). Skipping.", collection.count())
        return

    logger.info("Vector store is empty — seeding sample policies...")
    db = SessionLocal()

    try:
        for policy in SEED_POLICIES:
            chunks = chunk_by_section(policy["content"], policy["name"], policy["insurer"])
            texts = [c["text"] for c in chunks]
            embeddings = embed_texts(texts)

            collection.add(
                ids=[f"policy_{policy['id']}_chunk_{c['chunk_index']}" for c in chunks],
                embeddings=embeddings,
                metadatas=[{
                    "policy_id": str(policy["id"]),
                    "policy_name": policy["name"],
                    "insurer": policy["insurer"],
                    "section": c.get("section", "unknown"),
                    "chunk_index": c["chunk_index"],
                    "page_number": 1,
                } for c in chunks],
                documents=texts,
            )

            db.execute(text("""
                INSERT INTO policies (id, name, insurer, file_type, file_path, uploaded_by, is_active)
                VALUES (:id, :name, :insurer, 'txt', :path, 'system', true)
                ON CONFLICT (id) DO NOTHING
            """), {"id": policy["id"], "name": policy["name"],
                   "insurer": policy["insurer"], "path": f"seed/{policy['name']}.txt"})

            logger.info("Seeded: %s (%d chunks)", policy["name"], len(chunks))
            time.sleep(1)  # respect embedding rate limit

        db.commit()
        logger.info("Auto-seed complete. %d chunks in vector store.", collection.count())

    except Exception as e:
        logger.error("Auto-seed failed: %s", e)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _auto_seed()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered health insurance recommendation platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["Recommendations"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "aarogyaaid-backend"}
