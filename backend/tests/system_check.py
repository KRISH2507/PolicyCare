"""
system_check.py — Full system health check.
Run with: python tests/system_check.py
No server needed — tests all components directly.
"""
import json
import re
import sys

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []

def check(n, label, fn):
    try:
        fn()
        print(f"  {PASS}  {n}/7  {label}")
        results.append(True)
    except Exception as e:
        print(f"  {FAIL}  {n}/7  {label}")
        print(f"         Error: {e}")
        results.append(False)

print("\n=== AarogyaAid System Check ===\n")

# 1. PostgreSQL connection
def test_db_connect():
    from app.core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
check(1, "PostgreSQL (Neon) connected", test_db_connect)

# 2. Schema — email column present
def test_schema():
    from app.core.database import engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("users")]
    assert "email" in cols, f"email column missing. Got: {cols}"
    assert "username" not in cols, "old username column still present"
    tables = inspector.get_table_names()
    assert "policies" in tables
    assert "chat_sessions" in tables
check(2, "DB schema correct (email, no username, all tables)", test_schema)

# 3. Gemini embedding
def test_embedding():
    import google.generativeai as genai
    from app.core.config import settings
    genai.configure(api_key=settings.GEMINI_API_KEY)
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content="diabetes health insurance metro city",
        task_type="retrieval_query",
    )
    vec = result["embedding"]
    assert len(vec) == 3072, f"Expected 3072 dims, got {len(vec)}"
check(3, f"Gemini embedding (gemini-embedding-001, 3072 dims)", test_embedding)

# 4. Gemini generation
def test_generation():
    import google.generativeai as genai
    from app.core.config import settings
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    resp = model.generate_content('Return exactly this JSON: {"status": "ok"}')
    raw = resp.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    parsed = json.loads(raw)
    assert parsed.get("status") == "ok", f"Unexpected response: {parsed}"
check(4, "Gemini generation (gemini-2.0-flash, JSON mode)", test_generation)

# 5. JWT
def test_jwt():
    from app.core.security import create_access_token, decode_access_token
    token = create_access_token({"sub": "test@test.com", "role": "user"})
    decoded = decode_access_token(token)
    assert decoded["sub"] == "test@test.com"
    assert decoded["role"] == "user"
check(5, "JWT create + decode", test_jwt)

# 6. bcrypt
def test_bcrypt():
    from app.core.security import get_password_hash, verify_password
    h = get_password_hash("TestPass123")
    assert verify_password("TestPass123", h)
    assert not verify_password("wrong", h)
check(6, "bcrypt hash + verify", test_bcrypt)

# 7. Admin login flow (no HTTP — direct logic test)
def test_admin_logic():
    from app.core.config import settings
    from app.core.security import create_access_token, decode_access_token
    assert "@" in settings.ADMIN_EMAIL, "ADMIN_EMAIL must be an email address"
    assert len(settings.ADMIN_PASSWORD) >= 4, "ADMIN_PASSWORD too short"
    token = create_access_token({"sub": settings.ADMIN_EMAIL, "role": "admin"})
    decoded = decode_access_token(token)
    assert decoded["role"] == "admin"
    assert decoded["sub"] == settings.ADMIN_EMAIL
check(7, f"Admin config valid (email: {__import__('app.core.config', fromlist=['settings']).settings.ADMIN_EMAIL})", test_admin_logic)

# Summary
total = len(results)
passed = sum(results)
failed = total - passed
print(f"\n{'='*40}")
print(f"  {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  System is fully operational.")
else:
    print("  Fix the failed checks above before starting the server.")
print("="*40)
sys.exit(0 if failed == 0 else 1)
