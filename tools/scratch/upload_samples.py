import httpx
from pathlib import Path

sample_dir = Path("E:/SENTRY/sample_emails")
for eml_file in sample_dir.glob("*.eml"):
    with open(eml_file, "rb") as f:
        files = {"file": (eml_file.name, f, "message/rfc822")}
        r = httpx.post("http://localhost:8000/api/v1/emails/upload", files=files, timeout=30.0)
        print(f"Uploaded {eml_file.name}: status={r.status_code}")
        if r.status_code != 200:
            print("Error detail:", r.text)

r_emails = httpx.get("http://localhost:8000/api/v1/emails")
print(f"Total emails on server now: {len(r_emails.json())}")
