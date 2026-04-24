"""
seed_policies.py — Upload all 3 sample policy documents.
Run from backend/ directory:
    python seed_policies.py
"""
import urllib.request
import json
import os
import uuid
import sys

BASE = "http://localhost:8000"

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample-data")

POLICIES = [
    {
        "file": os.path.join(SAMPLE_DIR, "careshield_basic.txt"),
        "name": "CareShield Basic",
        "insurer": "SafeGuard General Insurance",
    },
    {
        "file": os.path.join(SAMPLE_DIR, "medprotect_plus.txt"),
        "name": "MedProtect Plus",
        "insurer": "HealthFirst Insurance Ltd.",
    },
    {
        "file": os.path.join(SAMPLE_DIR, "activecover_premier.txt"),
        "name": "ActiveCover Premier",
        "insurer": "VitalShield Health Insurance Ltd.",
    },
]


def get_admin_token():
    from app.core.config import settings
    data = json.dumps({
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/api/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["access_token"]


def upload_policy(token, filepath, name, insurer):
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "rb") as f:
        file_content = f.read()

    boundary = uuid.uuid4().hex
    filename = os.path.basename(filepath)

    body = b""
    for field, value in [("name", name), ("insurer", insurer)]:
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode()
    body += file_content
    body += f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}/api/admin/upload",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def main():
    print("\n=== Seeding Policy Database ===\n")

    try:
        token = get_admin_token()
        print("  Admin login: OK\n")
    except Exception as e:
        print(f"  FAIL: Could not get admin token: {e}")
        sys.exit(1)

    # Check existing
    req = urllib.request.Request(
        f"{BASE}/api/admin/policies",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        existing = json.loads(r.read())
    existing_names = {p["name"] for p in existing}
    print(f"  Existing policies: {len(existing)}")
    for n in existing_names:
        print(f"    - {n}")
    print()

    uploaded = 0
    for p in POLICIES:
        name = p["name"]
        if name in existing_names:
            print(f"  SKIP  {name} (already in database)")
            continue

        print(f"  Uploading: {name}")
        print(f"    Insurer : {p['insurer']}")
        print(f"    File    : {os.path.basename(p['file'])}")
        print(f"    Status  : parsing + embedding (10-30 seconds)...")

        try:
            result = upload_policy(token, p["file"], name, p["insurer"])
            print(f"    DONE    policy_id = {result['policy_id']}")
            uploaded += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"    FAIL    HTTP {e.code}: {body[:400]}")
        except Exception as e:
            print(f"    FAIL    {e}")
        print()

    # Final count
    req = urllib.request.Request(
        f"{BASE}/api/admin/policies",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        final = json.loads(r.read())

    print("=" * 45)
    print(f"  Uploaded this run : {uploaded}")
    print(f"  Total in database : {len(final)}")
    for p in final:
        print(f"    [{p['id']}] {p['name']}")
    print("=" * 45)

    if len(final) >= 3:
        print("\n  Database ready. Recommendations will now work.\n")
        print("  Test it:")
        print("  1. Go to http://localhost:5173")
        print("  2. Log in as a regular user")
        print("  3. Fill the profile form")
        print("  4. You should see a real recommendation\n")
    else:
        print(f"\n  Only {len(final)}/3 policies loaded. Check errors above.\n")


if __name__ == "__main__":
    main()
