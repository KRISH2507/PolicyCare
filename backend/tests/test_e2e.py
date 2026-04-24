"""
test_e2e.py — End-to-end recommendation + chat test.
Run with: python tests/test_e2e.py
Requires server on localhost:8000 with policies seeded.
"""
import urllib.request
import json
import sys
import os

BASE = "http://localhost:8000"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []


def check(label, passed, detail=""):
    tag = PASS if passed else FAIL
    print(f"  {tag}  {label}" + (f"\n         {detail}" if detail else ""))
    results.append(passed)


def post(path, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {}


def main():
    print("\n=== End-to-End Recommendation + Chat Test ===\n")

    # Get user token
    from app.core.config import settings
    s, b = post("/api/auth/login", {
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    token = b.get("access_token", "")
    check("Admin login", s == 200 and bool(token), f"status={s}")

    # Test profile: diabetes, metro, sedentary, 3-8L
    print("\n[ Recommendation — diabetes profile ]")
    profile = {
        "full_name": "Priya Sharma",
        "age": 34,
        "city_tier": "metro",
        "lifestyle": "sedentary",
        "pre_existing_conditions": ["diabetes"],
        "income_band": "3to8l"
    }
    print(f"  Profile: {profile['full_name']}, {profile['age']}y, {profile['city_tier']}, "
          f"{profile['pre_existing_conditions']}, {profile['income_band']}")
    print("  Calling /api/recommend/ (may take 10-20s)...")

    s, b = post("/api/recommend/", profile, token=token)
    check("Recommend returns 200", s == 200, f"status={s}")

    best_fit = b.get("best_fit")
    check("Has best_fit (not null)", best_fit is not None,
          f"best_fit={best_fit}")

    if best_fit:
        print(f"\n  Best fit: {best_fit.get('policy_name')} — {best_fit.get('insurer')}")
        print(f"  Premium:  {best_fit.get('premium')}")
        print(f"  Cover:    {best_fit.get('cover_amount')}")

    why = b.get("why_this_policy", "")
    check("why_this_policy is non-empty", len(why) > 50, f"length={len(why)}")
    if why:
        print(f"\n  Why: {why[:200]}...")

    peers = b.get("peer_comparison", [])
    check("peer_comparison has entries", len(peers) > 0, f"count={len(peers)}")
    if peers:
        print(f"\n  Peers: {[p['policy_name'] for p in peers]}")

    citations = b.get("citations", [])
    check("citations present", len(citations) > 0, f"citations={citations}")

    # Test profile: active, athlete
    print("\n[ Recommendation — active lifestyle profile ]")
    profile2 = {
        "full_name": "Rahul Verma",
        "age": 26,
        "city_tier": "metro",
        "lifestyle": "active",
        "pre_existing_conditions": [],
        "income_band": "8to15l"
    }
    print(f"  Profile: {profile2['full_name']}, {profile2['age']}y, {profile2['lifestyle']}")
    print("  Calling /api/recommend/ ...")
    s2, b2 = post("/api/recommend/", profile2, token=token)
    check("Active profile recommend returns 200", s2 == 200, f"status={s2}")
    check("Active profile has best_fit", b2.get("best_fit") is not None)
    if b2.get("best_fit"):
        print(f"  Best fit: {b2['best_fit']['policy_name']}")

    # Chat test
    if best_fit:
        print("\n[ Chat — question about recommended policy ]")
        print("  Question: 'What is the waiting period for diabetes?'")
        print("  Calling /api/chat/ ...")
        s3, b3 = post("/api/chat/", {
            "message": "What is the waiting period for diabetes under this plan?",
            "user_profile": profile,
            "recommended_policy_name": best_fit.get("policy_name", ""),
            "recommended_policy_id": None,
            "history": []
        }, token=token)
        check("Chat returns 200", s3 == 200, f"status={s3}")
        reply = b3.get("reply", "")
        check("Chat reply is non-empty", len(reply) > 20, f"length={len(reply)}")
        chat_citations = b3.get("citations", [])
        check("Chat has citations", len(chat_citations) > 0, f"citations={chat_citations}")
        if reply:
            print(f"\n  Reply: {reply[:300]}...")
        if chat_citations:
            print(f"  Citations: {chat_citations}")

    # Summary
    total = len(results)
    passed = sum(results)
    failed = total - passed
    print(f"\n{'='*45}")
    print(f"  {passed}/{total} passed  |  {failed} failed")
    if failed == 0:
        print("  Full recommendation + chat pipeline working!")
    else:
        print("  Some checks failed — see above.")
    print("="*45)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
