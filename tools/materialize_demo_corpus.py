import os
from pathlib import Path

sample_dir = Path("E:/SENTRY/sample_emails")
sample_dir.mkdir(parents=True, exist_ok=True)

emails = [
    # Campaign 1: Operation GhostRelay (CMP-2024-0034) - Indian Banking Credential Harvesting
    (
        "04_sbi_kyc_escalation.eml",
        """From: SBI NetBanking Care <alerts@onlinesbi-kyc-update.com>
To: victim.user@corporate.in
Subject: Final Notice: Immediate SBI YONO Access Termination Warning
Date: Mon, 15 Jan 2024 11:15:00 +0530
Message-ID: <20240115111500.8372.qmail@onlinesbi-kyc-update.com>
Received: from mx.corporate.in (10.0.0.1) by mail.corporate.in; Mon, 15 Jan 2024 11:15:05 +0530
Received: from relay01.f3netze.de (185.220.101.5) by mx.corporate.in with ESMTP; Mon, 15 Jan 2024 11:15:02 +0530
Received: from authenticated-user (185.220.101.5) by relay01.f3netze.de; Mon, 15 Jan 2024 11:15:00 +0530
Authentication-Results: mx.corporate.in; spf=softfail (sender IP 185.220.101.5); dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear State Bank of India Customer,</p>
<p>Your SBI YONO online netbanking privileges are scheduled for immediate suspension within 12 hours due to pending mandatory KYC documentation under RBI mandate 2024.</p>
<p>Please update your Aadhaar and PAN card details immediately via our secure server: <a href="http://sbi-secureverify.com/portal/login">https://www.onlinesbi.sbi/kyc-update</a></p>
<p>Failure to comply will result in permanent account freezing.</p>
"""
    ),
    (
        "05_hdfc_netbanking_token.eml",
        """From: HDFC Security Desk <security@hdfc-netbanking-alert.xyz>
To: target.analyst@enterprise.com
Subject: Security Alert: High Value Transaction Authorization Required
Date: Mon, 15 Jan 2024 09:30:00 +0530
Message-ID: <20240115093000.91823.smtp@hdfc-netbanking-alert.xyz>
Received: from mx.enterprise.com (10.0.1.2) by internal.enterprise.com; Mon, 15 Jan 2024 09:30:08 +0530
Received: from mail.jonasbunde-vps.net (194.26.29.117) by mx.enterprise.com with ESMTP; Mon, 15 Jan 2024 09:30:04 +0530
Authentication-Results: mx.enterprise.com; spf=fail (IP 194.26.29.117); dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear HDFC Customer,</p>
<p>An outgoing IMPS fund transfer of INR 4,85,000.00 is currently pending your authorization token on device iPhone 14 Pro.</p>
<p>If you did not initiate this transfer, cancel the transaction immediately: <a href="http://hdfc-netbanking-alert.xyz/cancel-tx">https://netbanking.hdfcbank.com/dispute</a></p>
"""
    ),
    (
        "06_icici_pan_link_phish.eml",
        """From: ICICI Bank Alert <no-reply@icicibank-update-portal.com>
To: accounts.payable@victim-domain.in
Subject: Mandatory Action: ICICI iMobile Pay Account Verification
Date: Sun, 14 Jan 2024 16:45:00 +0530
Message-ID: <20240114164500.5512.mail@icicibank-update-portal.com>
Received: from mx1.victim-domain.in (10.2.0.1) by mail.victim-domain.in; Sun, 14 Jan 2024 16:45:06 +0530
Received: from tor-node-nl.f3netze.de (185.220.101.34) by mx1.victim-domain.in with ESMTP; Sun, 14 Jan 2024 16:45:02 +0530
Authentication-Results: mx1.victim-domain.in; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Valued Customer,</p>
<p>Link your PAN card to ICICI iMobile NetBanking to maintain active debit card privileges before midnight.</p>
<p>Login securely: <a href="http://icicibank-update-portal.com/auth">https://infinity.icicibank.com/login</a></p>
"""
    ),
    (
        "07_rbi_statutory_directive.eml",
        """From: Reserve Bank Compliance <circulars@rbi-statutory-notice.org>
To: compliance.officer@bank-entity.in
Subject: STATUTORY ORDER: Mandatory Fraud Auditing of Dormant Beneficiaries
Date: Mon, 15 Jan 2024 08:00:00 +0530
Message-ID: <20240115080000.1102.qmail@rbi-statutory-notice.org>
Received: from mx.bank-entity.in (10.0.0.5) by mail.bank-entity.in; Mon, 15 Jan 2024 08:00:05 +0530
Received: from tor-exit-de.f3netze.de (185.220.102.8) by mx.bank-entity.in with ESMTP; Mon, 15 Jan 2024 08:00:02 +0530
Authentication-Results: mx.bank-entity.in; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>All scheduled commercial banks must review the attached statutory annexure and verify RTGS clearing portals immediately.</p>
<p>Access Directive Annexure: <a href="http://sbi-secureverify.com/rbi-directive">https://rbi.org.in/notifications/2024</a></p>
"""
    ),
    (
        "08_sbi_reward_points_lure.eml",
        """From: SBI Card Rewards <rewards@onlinesbi-kyc-update.com>
To: user.cardholder@indiamail.in
Subject: Congratulations! You have INR 9,850 Unclaimed SBI Reward Points Expiring Today
Date: Sun, 14 Jan 2024 19:20:00 +0530
Message-ID: <20240114192000.7812.smtp@onlinesbi-kyc-update.com>
Received: from mx.indiamail.in (10.1.1.1) by mail.indiamail.in; Sun, 14 Jan 2024 19:20:04 +0530
Received: from tor-relay02.f3netze.de (185.220.101.9) by mx.indiamail.in with ESMTP; Sun, 14 Jan 2024 19:20:02 +0530
Authentication-Results: mx.indiamail.in; spf=softfail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear SBI Cardholder,</p>
<p>Your accumulated 19,700 SBI Reward Points worth INR 9,850 are set to expire tonight. Redeem directly into your bank account:</p>
<p><a href="http://sbi-secureverify.com/rewards/claim">https://www.sbicard.com/redeem-now</a></p>
"""
    ),
    (
        "09_hdfc_credit_limit_scam.eml",
        """From: HDFC Bank Credit Division <limit-enhancement@hdfc-netbanking-alert.xyz>
To: premium.client@corporatemail.com
Subject: Instant Approval: Pre-Approved Credit Card Limit Enhancement to INR 10,00,000
Date: Mon, 15 Jan 2024 12:40:00 +0530
Message-ID: <20240115124000.3341.smtp@hdfc-netbanking-alert.xyz>
Received: from mx.corporatemail.com (10.0.0.2) by mail.corporatemail.com; Mon, 15 Jan 2024 12:40:06 +0530
Received: from vps-nl.jonasbunde-vps.net (194.26.29.120) by mx.corporatemail.com with ESMTP; Mon, 15 Jan 2024 12:40:03 +0530
Authentication-Results: mx.corporatemail.com; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Congratulations! You are eligible for an instant zero-fee credit limit increase to INR 10,00,000.</p>
<p>Claim pre-approved offer: <a href="http://hdfc-netbanking-alert.xyz/credit-boost">https://mycards.hdfcbank.com/limit-upgrade</a></p>
"""
    ),
    (
        "10_axis_urgent_unblock.eml",
        """From: Axis Bank Online Desk <alerts@axis-bank-verify.com>
To: customer.ops@enterprisemail.in
Subject: Security Notice: Axis Internet Banking Account Temporarily Locked
Date: Mon, 15 Jan 2024 14:00:00 +0530
Message-ID: <20240115140000.9981.mail@axis-bank-verify.com>
Received: from mx.enterprisemail.in (10.0.0.4) by mail.enterprisemail.in; Mon, 15 Jan 2024 14:00:05 +0530
Received: from relay01.f3netze.de (185.220.101.5) by mx.enterprisemail.in with ESMTP; Mon, 15 Jan 2024 14:00:02 +0530
Authentication-Results: mx.enterprisemail.in; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Customer, your Axis Bank internet banking ID has been temporarily locked after 3 failed password attempts.</p>
<p>Unlock your account now: <a href="http://sbi-secureverify.com/axis/unlock">https://omni.axisbank.co.in/axisretail/unlock</a></p>
"""
    ),

    # Campaign 2: Titan Executive BEC Syndicate (CMP-2024-0012) - Executive Impersonation & Wire Fraud
    (
        "11_bec_payroll_reroute.eml",
        """From: Richard Mercer <ceo.mercer.corp@gmail.com>
Reply-To: exec.rmercer@executive-corp-mail.com
To: hr.payroll@mercertech.com
Subject: Urgent: Updated Direct Deposit / Remittance Account for January Payroll
Date: Mon, 15 Jan 2024 07:15:00 -0500
Message-ID: <20240115071500.1293.smtp@executive-corp-mail.com>
Received: from mx.mercertech.com (10.0.0.1) by mail.mercertech.com; Mon, 15 Jan 2024 07:15:05 -0500
Received: from mail-relay.vpnsubnets.com (198.51.100.42) by mx.mercertech.com with ESMTP; Mon, 15 Jan 2024 07:15:02 -0500
Authentication-Results: mx.mercertech.com; spf=softfail; dkim=none; dmarc=fail
Content-Type: text/plain; charset="utf-8"

Hi Payroll Team,

I have recently switched my primary checking account to a new private banking facility.
Please update my direct deposit allocation for this upcoming January pay cycle immediately to avoid bounced disbursement.

New Routing Number: 021000021
Account Number: 883921094812
Bank Name: Chase Private Client

Please confirm once the change is posted in ADP.

Best regards,
Richard Mercer
Chief Executive Officer
Mercer Technologies Corp
"""
    ),
    (
        "12_bec_confidential_audit.eml",
        """From: Elena Rostova - Board Chair <elena.board.chair@management-board-review.com>
To: cfo.davidson@mercertech.com
Subject: STRICTLY CONFIDENTIAL // Acquisition Escrow Funding Instructions
Date: Mon, 15 Jan 2024 06:45:00 -0500
Message-ID: <20240115064500.8712.qmail@management-board-review.com>
Received: from mx.mercertech.com (10.0.0.1) by mail.mercertech.com; Mon, 15 Jan 2024 06:45:06 -0500
Received: from vpn-gw.commercialvpn.net (198.51.100.88) by mx.mercertech.com with ESMTP; Mon, 15 Jan 2024 06:45:02 -0500
Authentication-Results: mx.mercertech.com; spf=fail; dkim=none; dmarc=fail
Content-Type: text/plain; charset="utf-8"

Mark,

The special M&A committee has authorized the initial deposit of $4,250,000 into the international escrow vehicle.
Due to regulatory disclosure embargoes, do not mention this transfer on Slack or standard internal channels until our 8-K filing is cleared tomorrow.

Please process the wire transfer according to the attached coordinates immediately.

Regards,
Elena Rostova
Chair of the Executive Board
"""
    ),
    (
        "13_bec_vendor_invoice_swap.eml",
        """From: Accounts Receivable <billing@acme-cloudsystems-corp.com>
To: accounts.payable@enterprise-client.com
Subject: URGENT: Updated Banking Coordinates for Invoice #INV-2024-8841 ($184,500.00)
Date: Mon, 15 Jan 2024 10:00:00 -0500
Message-ID: <20240115100000.4412.mail@acme-cloudsystems-corp.com>
Received: from mx.enterprise-client.com (10.0.0.1) by mail.enterprise-client.com; Mon, 15 Jan 2024 10:00:05 -0500
Received: from relay02.vpnsubnets.com (198.51.100.99) by mx.enterprise-client.com with ESMTP; Mon, 15 Jan 2024 10:00:02 -0500
Authentication-Results: mx.enterprise-client.com; spf=fail; dkim=none; dmarc=fail
Content-Type: text/plain; charset="utf-8"

Attention Accounts Payable,

Please note our company bank accounts have been migrated to HSBC Premier Corporate Banking.
Please disburse payment for overdue invoice #INV-2024-8841 ($184,500.00) to the following coordinates today:

IBAN: GB29HBUK40127684920192
BIC/SWIFT: HBUKGB41XXX
Beneficiary: ACME Cloud Systems Overseas Ltd

Thank you,
Finance Operations Team
"""
    ),
    (
        "14_bec_giftcard_expedite.eml",
        """From: Richard Mercer <ceo.mercer.corp@gmail.com>
To: executive.assistant@mercertech.com
Subject: Quick Task // Client Appreciation Cards Needed Right Away
Date: Mon, 15 Jan 2024 13:10:00 -0500
Message-ID: <20240115131000.1192.smtp@gmail.com>
Received: from mx.mercertech.com (10.0.0.1) by mail.mercertech.com; Mon, 15 Jan 2024 13:10:05 -0500
Received: from mail-sor-f65.google.com (209.85.220.65) by mx.mercertech.com with ESMTP; Mon, 15 Jan 2024 13:10:02 -0500
Authentication-Results: mx.mercertech.com; spf=pass; dkim=pass; dmarc=pass
Content-Type: text/plain; charset="utf-8"

Are you at your desk right now?

I am currently in an all-day executive board meeting and need you to urgently purchase 10 Apple e-Gift cards ($500 each) for our visiting key enterprise clients.
Please charge them to the corporate purchasing card, scratch the codes, and email the digital voucher numbers back to me as soon as possible.

Do not call me as I cannot pick up during the presentation.

Thanks,
Richard
"""
    ),

    # Campaign 3: FinPhish Global Cloud Harvester (CMP-2024-0089) - SaaS OAuth & Document Phishing
    (
        "15_docusign_nda_token_steal.eml",
        """From: DocuSign Signature Service <service@docusign-secure-review.com>
To: legal.counsel@enterprise.com
Subject: Please DocuSign: Mutual Non-Disclosure Agreement & Partnership Termsheet.pdf
Date: Mon, 15 Jan 2024 09:12:00 +0000
Message-ID: <20240115091200.7723.smtp@docusign-secure-review.com>
Received: from mx.enterprise.com (10.0.0.1) by mail.enterprise.com; Mon, 15 Jan 2024 09:12:05 +0000
Received: from mail.cloudflare-relay-proxy.net (104.21.45.12) by mx.enterprise.com with ESMTP; Mon, 15 Jan 2024 09:12:02 +0000
Authentication-Results: mx.enterprise.com; spf=softfail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<div style="font-family: Arial, sans-serif;">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/DocuSign_logo.svg/320px-DocuSign_logo.svg.png" width="120" />
  <h3>DocuSign Electronic Signature Notification</h3>
  <p>Robert Sterling sent you a document to review and sign before 5:00 PM GMT.</p>
  <p><a href="http://docusign-secure-review.com/oauth/authorize?scope=offline_access" style="background:#2563EB;color:#fff;padding:10px 20px;text-decoration:none;border-radius:4px;">REVIEW DOCUMENT</a></p>
  <p><small>Powered by DocuSign Cloud Enterprise Infrastructure.</small></p>
</div>
"""
    ),
    (
        "16_m365_password_expiry_phish.eml",
        """From: Microsoft Security Team <no-reply@office365-security-portal.net>
To: analyst.j@cloud-defense.io
Subject: Microsoft 365: Urgent Password Expiration Notice for analyst.j@cloud-defense.io
Date: Mon, 15 Jan 2024 08:45:00 +0000
Message-ID: <20240115084500.5519.mail@office365-security-portal.net>
Received: from mx.cloud-defense.io (10.0.0.1) by mail.cloud-defense.io; Mon, 15 Jan 2024 08:45:05 +0000
Received: from proxy.cloudflare-fastflux.net (172.67.182.90) by mx.cloud-defense.io with ESMTP; Mon, 15 Jan 2024 08:45:02 +0000
Authentication-Results: mx.cloud-defense.io; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<div style="font-family: Segoe UI, Tahoma, sans-serif;">
  <h2>Microsoft 365 Organization Alert</h2>
  <p>Your domain password for account <b>analyst.j@cloud-defense.io</b> expires in 2 hours.</p>
  <p>To retain current login credentials and prevent mailbox suspension, keep your existing password:</p>
  <p><a href="http://office365-security-portal.net/login/keep-password">Keep Current Password</a></p>
</div>
"""
    ),
    (
        "17_google_workspace_oauth.eml",
        """From: Google Workspace Security <no-reply@workspace-auth-verify.com>
To: admin.sec@startuphub.io
Subject: Security Notice: Review Third-Party Access Request for Google Drive
Date: Mon, 15 Jan 2024 10:30:00 +0000
Message-ID: <20240115103000.9941.smtp@workspace-auth-verify.com>
Received: from mx.startuphub.io (10.0.0.1) by mail.startuphub.io; Mon, 15 Jan 2024 10:30:05 +0000
Received: from edge-fastflux.net (104.21.89.201) by mx.startuphub.io with ESMTP; Mon, 15 Jan 2024 10:30:02 +0000
Authentication-Results: mx.startuphub.io; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>A new third-party application "DocuSync Integration Pro" was granted full read/write permission to your Google Drive and Gmail messages.</p>
<p>If you did not authorize this access, revoke permissions immediately:</p>
<p><a href="http://workspace-auth-verify.com/security/revoke">https://myaccount.google.com/permissions</a></p>
"""
    ),
    (
        "18_sharepoint_secure_file.eml",
        """From: SharePoint Notification <files@docusign-secure-review.com>
To: finance.lead@enterprise.com
Subject: SharePoint Online: Q4 Executive Compensation Summary.pdf.exe shared with you
Date: Mon, 15 Jan 2024 11:00:00 +0000
Message-ID: <20240115110000.4419.smtp@docusign-secure-review.com>
Received: from mx.enterprise.com (10.0.0.1) by mail.enterprise.com; Mon, 15 Jan 2024 11:00:05 +0000
Received: from mail.cloudflare-relay-proxy.net (104.21.45.12) by mx.enterprise.com with ESMTP; Mon, 15 Jan 2024 11:00:02 +0000
Authentication-Results: mx.enterprise.com; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>A confidential document <b>Q4_Executive_Compensation_Dossier_Final.pdf&#8238;cod.exe</b> has been shared via secure SharePoint storage.</p>
<p><a href="http://docusign-secure-review.com/download/sharepoint-dossier">Download Secure Document</a></p>
"""
    )
]

for filename, content in emails:
    file_path = sample_dir / filename
    file_path.write_text(content.strip(), encoding="utf-8")
    print(f"  [+] Created demo EML: {file_path}")

print(f"\n[OK] Materialized {len(emails)} curated demo EMLs across 3 campaign clusters.")
