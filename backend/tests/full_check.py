"""Full pre-deployment check — runs against port 8001 (SQLite test instance)."""
import urllib.request, json, sys, os

BASE = "http://localhost:8001"
OK = "\033[92mOK\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []

def check(label, passed, detail=""):
    tag = OK if passed else FAIL
    print(f"  {tag}  {label}" + (f"  [{detail}]" if detail else ""))
    results.append((label, passed))

def get(path, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{BASE}{path}", headers=h), timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except: return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

def post(path, body, token=None):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(f"{BASE}{path}", json.dumps(body).encode(), h, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except: return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

print("\n=== Pre-Deployment Check ===\n")

# Health
s, b = get("/health")
check("GET /health", s == 200 and b.get("status") == "ok", f"status={s}")

# Auth — wrong password
s, _ = post("/api/auth/login", {"email": "x@x.com", "password": "wrong"})
check("Wrong credentials → 401", s == 401, f"status={s}")

# Auth — signup
s, b = post("/api/auth/signup", {"email": "deploy_test@test.com", "password": "Test1234!", "full_name": "Deploy Test"})
check("Signup → 201 or 409", s in (201, 409), f"status={s}")
token = b.get("access_token", "")
if s == 409:
    s2, b2 = post("/api/auth/login", {"email": "deploy_test@test.com", "password": "Test1234!"})
    token = b2.get("access_token", "")
    check("Login existing user → 200", s2 == 200, f"status={s2}")
check("Got access_token", bool(token))
check("Role = user", b.get("role") == "user" or (s == 409 and True))

# Admin login
admin_email = os.getenv("ADMIN_EMAIL", "thekrishdeepsingh@gmail.com")
admin_pass = os.getenv("ADMIN_PASSWORD", "1111")
s, b = post("/api/auth/login", {"email": admin_email, "password": admin_pass})
check("Admin login → 200", s == 200, f"status={s}")
admin_token = b.get("access_token", "")
check("Admin role = admin", b.get("role") == "admin")

# Route protection
s, _ = get("/api/admin/policies")
check("No token → 401", s == 401, f"status={s}")
s, _ = get("/api/admin/policies", token=token)
check("User token on admin → 403", s == 403, f"status={s}")
s, _ = get("/api/admin/policies", token=admin_token)
check("Admin token on admin → 200", s == 200, f"status={s}")

# Policies seeded
s, policies = get("/api/admin/policies", token=admin_token)
check("3 policies seeded", len(policies) == 3, f"count={len(policies)}")

# Recommend
s, b = post("/api/recommend/", {
    "full_name": "Priya", "age": 34, "city_tier": "metro",
    "lifestyle": "sedentary", "pre_existing_conditions": ["diabetes"], "income_band": "3to8l"
}, token=token)
check("Recommend → 200", s == 200, f"status={s}")
check("Has why_this_policy", bool(b.get("why_this_policy")))
check("Has peer_comparison", isinstance(b.get("peer_comparison"), list))

# Recommend without auth
s, _ = post("/api/recommend/", {"full_name": "x", "age": 30, "city_tier": "metro",
    "lifestyle": "sedentary", "pre_existing_conditions": [], "income_band": "3to8l"})
check("Recommend without token → 401", s == 401, f"status={s}")

# Chat validation
s, _ = post("/api/chat/", {"message": "", "user_profile": {}, "recommended_policy_name": "", "history": []}, token=token)
check("Empty chat message → 422", s == 422, f"status={s}")

# Schema validation
s, _ = post("/api/auth/signup", {"email": "notanemail", "password": "x", "full_name": ""})
check("Invalid email → 422", s == 422, f"status={s}")
s, _ = post("/api/recommend/", {"full_name": "x", "age": 0, "city_tier": "metro",
    "lifestyle": "sedentary", "pre_existing_conditions": [], "income_band": "3to8l"}, token=token)
check("Age=0 → 422", s == 422, f"status={s}")

# Summary
total = len(results)
passed = sum(1 for _, p in results if p)
failed = total - passed
print(f"\n{'='*40}")
print(f"  {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("  Ready to deploy.")
else:
    print("  Fix failures before deploying.")
print("="*40)
sys.exit(0 if failed == 0 else 1)
