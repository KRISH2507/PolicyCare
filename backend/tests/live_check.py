"""
live_check.py — Live endpoint tests against running server.
Run with: python tests/live_check.py
Requires server on localhost:8000.
"""
import urllib.request
import json
import sys
import os

BASE = "http://localhost:8000"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []
n = [0]

def check(label, passed, detail=""):
    n[0] += 1
    tag = PASS if passed else FAIL
    print(f"  {tag}  {n[0]:02d}  {label}" + (f"  [{detail}]" if detail else ""))
    results.append(passed)

def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

def post(path, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

print("\n=== AarogyaAid Live Endpoint Check ===\n")

# ── Health ──
print("[ Health ]")
s, b = get("/health")
check("/health returns 200", s == 200, f"status={s}")
check("status=ok", b.get("status") == "ok")

# ── Auth: wrong password ──
print("\n[ Auth — wrong credentials ]")
s, b = post("/api/auth/login", {"email": "admin@wrong.com", "password": "bad"})
check("Wrong email returns 401", s == 401, f"status={s}")

# ── Auth: admin login ──
print("\n[ Auth — admin login ]")
admin_email = os.getenv("ADMIN_EMAIL", "thekrishdeepsingh@gmail.com")
admin_pass  = os.getenv("ADMIN_PASSWORD", "1111")
s, b = post("/api/auth/login", {"email": admin_email, "password": admin_pass})
check("Admin login returns 200", s == 200, f"status={s}")
check("Admin has access_token", "access_token" in b)
check("Admin role=admin", b.get("role") == "admin")
admin_token = b.get("access_token", "")

# ── Auth: new user signup ──
print("\n[ Auth — user signup ]")
test_email = "qatest_live@aarogyaaid.com"
s, b = post("/api/auth/signup", {
    "email": test_email,
    "password": "TestPass123!",
    "full_name": "QA Test User"
})
# 201 = new user, 409 = already exists (both fine)
check("Signup returns 201 or 409", s in (201, 409), f"status={s}")
if s == 201:
    user_token = b.get("access_token", "")
    check("Signup returns access_token", bool(user_token))
    check("Signup role=user", b.get("role") == "user")
    check("Signup returns email", b.get("email") == test_email)
else:
    # Already exists — login instead
    s2, b2 = post("/api/auth/login", {"email": test_email, "password": "TestPass123!"})
    user_token = b2.get("access_token", "")
    check("Existing user login works", s2 == 200, f"status={s2}")
    check("Login returns access_token", bool(user_token))
    check("Login role=user", b2.get("role") == "user")

# ── Route protection ──
print("\n[ Route Protection ]")
s, _ = get("/api/admin/policies")
check("No-token admin blocked (401)", s == 401, f"status={s}")

s, _ = get("/api/admin/policies", token=user_token)
check("User-token admin blocked (403)", s == 403, f"status={s}")

s, _ = get("/api/admin/policies", token=admin_token)
check("Admin-token allowed (200)", s == 200, f"status={s}")

# ── Recommend (no policies yet — graceful fallback) ──
print("\n[ Recommendation Engine ]")
profile = {
    "full_name": "Priya Sharma",
    "age": 34,
    "city_tier": "metro",
    "lifestyle": "sedentary",
    "pre_existing_conditions": ["diabetes"],
    "income_band": "3to8l"
}
s, b = post("/api/recommend/", profile, token=user_token)
check("Recommend returns 200", s == 200, f"status={s}")
check("Has why_this_policy", isinstance(b.get("why_this_policy"), str) and len(b.get("why_this_policy","")) > 0)
check("Has peer_comparison list", isinstance(b.get("peer_comparison"), list))
check("Has citations list", isinstance(b.get("citations"), list))

# ── Recommend without auth ──
s, _ = post("/api/recommend/", profile)
check("Recommend without token blocked (401)", s == 401, f"status={s}")

# ── Chat validation ──
print("\n[ Chat Validation ]")
s, b = post("/api/chat/", {
    "message": "",
    "user_profile": profile,
    "recommended_policy_name": "Test",
    "history": []
}, token=user_token)
check("Empty message returns 422", s == 422, f"status={s}")

# ── Admin policies list ──
print("\n[ Admin Policies ]")
s, b = get("/api/admin/policies", token=admin_token)
check("GET /admin/policies returns list", isinstance(b, list), f"count={len(b) if isinstance(b,list) else '?'}")

# ── Summary ──
total = len(results)
passed = sum(results)
failed = total - passed
print(f"\n{'='*45}")
print(f"  {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  All endpoints working correctly.")
else:
    print("  Some checks failed — see above.")
print("="*45)
sys.exit(0 if failed == 0 else 1)
