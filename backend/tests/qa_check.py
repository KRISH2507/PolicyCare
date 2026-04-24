"""
qa_check.py — Live endpoint QA script.
Run with: python tests/qa_check.py
Requires the backend to be running on localhost:8000.
"""
import urllib.request
import json
import os
import sys

BASE = "http://localhost:8000"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

results = []

def check(label, passed, detail=""):
    tag = PASS if passed else FAIL
    print(f"  {tag}  {label}" + (f"  [{detail}]" if detail else ""))
    results.append(passed)

def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {}

def post(path, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {}
    except Exception as e:
        return 0, {}

print("\n=== AarogyaAid Live QA Check ===\n")

# ── 1. Health ──
print("[ Health ]")
status, body = get("/health")
check("/health returns 200", status == 200, f"status={status}")
check("/health has status:ok", body.get("status") == "ok")

# ── 2. Auth ──
print("\n[ Auth ]")
status, body = post("/api/auth/login", {"username": "admin", "password": "wrongpass"})
check("Wrong password returns 401", status == 401, f"status={status}")

admin_user = os.getenv("ADMIN_USERNAME", "admin")
admin_pass = os.getenv("ADMIN_PASSWORD", "adminpass")
status, body = post("/api/auth/login", {"username": admin_user, "password": admin_pass})
check("Admin login returns 200", status == 200, f"status={status}")
check("Admin login returns access_token", "access_token" in body)
check("Admin login returns role=admin", body.get("role") == "admin")
admin_token = body.get("access_token", "")

status, body = post("/api/auth/login", {"username": "newqauser99", "password": "testpass"})
check("New user auto-registers (200)", status == 200, f"status={status}")
check("New user gets role=user", body.get("role") == "user")
user_token = body.get("access_token", "")

# ── 3. Route protection ──
print("\n[ Route Protection ]")
status, _ = get("/api/admin/policies")
check("No-token admin request blocked (401)", status == 401, f"status={status}")

status, _ = get("/api/admin/policies", token=user_token)
check("User-token admin request blocked (403)", status == 403, f"status={status}")

status, _ = get("/api/admin/policies", token=admin_token)
check("Admin-token admin request allowed (200)", status == 200, f"status={status}")

# ── 4. Recommend with no policies ──
print("\n[ Recommendation Engine ]")
profile = {
    "full_name": "QA Test User",
    "age": 30,
    "city_tier": "metro",
    "lifestyle": "sedentary",
    "pre_existing_conditions": [],
    "income_band": "3to8l"
}
status, body = post("/api/recommend/", profile, token=user_token)
check("Recommend returns 200", status == 200, f"status={status}")
check("Recommend has why_this_policy", "why_this_policy" in body)
check("Recommend has peer_comparison list", isinstance(body.get("peer_comparison"), list))
check("Recommend has citations list", isinstance(body.get("citations"), list))

# ── 5. Recommend edge cases ──
print("\n[ Recommendation Edge Cases ]")
bad_profile = {"full_name": "", "age": 0, "city_tier": "metro", "lifestyle": "sedentary",
               "pre_existing_conditions": [], "income_band": "3to8l"}
status, body = post("/api/recommend/", bad_profile, token=user_token)
# age=0 is invalid per schema (int, but no min constraint server-side — just checking it doesn't crash)
check("age=0 profile doesn't crash server (returns 200 or 422)", status in (200, 422), f"status={status}")

# ── 6. Chat ──
print("\n[ Chat Engine ]")
chat_payload = {
    "message": "What is the waiting period?",
    "user_profile": profile,
    "recommended_policy_name": "Test Policy",
    "recommended_policy_id": None,
    "history": []
}
status, body = post("/api/chat/", chat_payload, token=user_token)
check("Chat returns 200", status == 200, f"status={status}")
check("Chat has reply field", "reply" in body)
check("Chat has citations list", isinstance(body.get("citations"), list))
check("Chat has requires_followup bool", isinstance(body.get("requires_followup"), bool))

# Empty message
chat_payload["message"] = ""
status, body = post("/api/chat/", chat_payload, token=user_token)
check("Empty chat message returns 422 (validation)", status == 422, f"status={status}")

# ── 7. Admin policies ──
print("\n[ Admin Policies ]")
status, policies = get("/api/admin/policies", token=admin_token)
check("GET /admin/policies returns list", isinstance(policies, list), f"count={len(policies)}")

# ── Summary ──
total = len(results)
passed = sum(results)
failed = total - passed
print(f"\n{'='*40}")
print(f"Results: {passed}/{total} passed  |  {failed} failed")
if failed == 0:
    print("All checks passed. Backend is healthy.")
else:
    print(f"{failed} check(s) failed — review output above.")
print('='*40)
sys.exit(0 if failed == 0 else 1)
