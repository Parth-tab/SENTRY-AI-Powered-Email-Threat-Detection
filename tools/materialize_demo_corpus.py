import os
import shutil
from pathlib import Path

sample_dir = Path("E:/SENTRY/sample_emails")

# Clean existing directory to prevent orphaned old-brand EMLs
if sample_dir.exists():
    for f in sample_dir.glob("*.eml"):
        try:
            f.unlink()
        except Exception:
            pass
else:
    sample_dir.mkdir(parents=True, exist_ok=True)

emails = [
    # Baseline Threat 1: Tor Relay Credential Harvester (Apex National Bank)
    (
        "apex_phishing_tor_relay.eml",
        """Delivered-To: target-customer@gmail.com
Received: by 2002:a05:6512:301:0:0:0:0 with SMTP id x1csp1029341;
        Mon, 15 Jan 2024 10:23:48 +0000 (UTC)
Authentication-Results: mx.google.com;
       dkim=none;
       spf=fail (google.com: domain of support@apex-secureverify.com does not designate 185.220.101.34 as permitted sender) smtp.mailfrom=support@apex-secureverify.com;
       dmarc=fail (p=REJECT dis=REJECT) header.from=apexbank.internal
Received: from mail.bulletproof-relay.net (mail.bulletproof-relay.net [185.220.101.34])
        by mx.google.com with ESMTP id z4si8192342plk.14.2024.01.15.10.23.47
        for <target-customer@gmail.com>;
        Mon, 15 Jan 2024 10:23:47 +0000 (UTC)
Received: from unknown (HELO tor-exit-node-ams.f3netze.de) (185.220.101.34)
        by mail.bulletproof-relay.net with ESMTP; Mon, 15 Jan 2024 10:23:45 +0000
Message-ID: <20240115102345.92841.qmail@apex-secureverify.com>
Date: Mon, 15 Jan 2024 10:23:40 +0000
From: "Apex National Bank Security Team" <support@apex-secureverify.com>
Reply-To: "Apex Verification Desk" <no-reply@onlineapex-kyc-update.com>
Return-Path: <bounce@unauthorized-smtp-server.xyz>
To: target-customer@gmail.com
Subject: URGENT: Mandatory KYC Verification Required Within 24 Hours or Account Suspended
X-Originating-IP: [185.220.101.34]
X-Mailer: PHPMailer 6.1.4 (https://github.com/PHPMailer/PHPMailer)
Content-Type: text/html; charset="UTF-8"

<!DOCTYPE html>
<html>
<head><title>Apex Alert</title></head>
<body style="font-family: Arial, sans-serif; color: #333;">
  <div style="border: 2px solid #b91c1c; padding: 20px; border-radius: 8px;">
    <h2 style="color: #b91c1c;">Apex National Bank — Security Notification</h2>
    <p>Dear Valued Customer,</p>
    <p>We detected unauthorized login attempts on your NetBanking account from an unrecognized IP address. In accordance with National Banking Regulatory Board security directives, your account access has been temporarily restricted.</p>
    <p><strong>ACTION REQUIRED:</strong> You must immediately verify your credentials and update your KYC documents within 24 hours to avoid permanent account deactivation.</p>
    <p style="text-align: center; margin: 25px 0;">
      <a href="https://apex-secureverify.com/login" style="background-color: #0284c7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
        Click Here to Verify Your Account (https://online.apexbank.internal/login)
      </a>
    </p>
    <p>Failure to complete verification will result in immediate suspension of all debit card and wire transfer privileges.</p>
    <br/>
    <p style="font-size: 12px; color: #666;">This is an automated notification. Please do not reply directly to this email.</p>
    <p style="font-size: 11px; color: #999;">Reference ID: APEX-SEC-2024-01-15-88419</p>
  </div>
</body>
</html>"""
    ),

    # Baseline Threat 2: Executive Wire Fraud BEC
    (
        "bec_executive_wire_fraud.eml",
        """Delivered-To: accountant@mercertech.com
Received: by 2002:a17:902:838b:0:0:0:0 with SMTP id b11csp4829103;
        Mon, 15 Jan 2024 07:15:22 -0500 (EST)
Authentication-Results: mx.mercertech.com;
       dkim=pass header.i=@gmail.com;
       spf=pass smtp.mailfrom=ceo.mercer.corp@gmail.com;
       dmarc=pass (p=NONE) header.from=gmail.com
Received: from mail-sor-f65.google.com (mail-sor-f65.google.com [209.85.220.65])
        by mx.mercertech.com with ESMTP id p18si4910283wmc.21.2024.01.15.07.15.21
        for <accountant@mercertech.com>;
        Mon, 15 Jan 2024 07:15:21 -0500 (EST)
Message-ID: <CABhZ=8xK2=1092819038@mail.gmail.com>
Date: Mon, 15 Jan 2024 07:15:18 -0500
From: "Richard Mercer (CEO)" <ceo.mercer.corp@gmail.com>
Reply-To: "Richard Mercer" <exec.rmercer@executive-corp-mail.com>
To: accountant@mercertech.com
Subject: URGENT: Confidential Acquisition Wire Transfer ($1.25M)
Content-Type: text/plain; charset="UTF-8"

Good morning,

I am currently in an urgent off-site board meeting regarding our Project Apex acquisition. 

We need to process an immediate, time-sensitive closing wire of $1,250,000.00 to our external legal escrow partners today before 11:00 AM EST.

Please find the wiring instructions below:
Beneficiary: Apex Global Escrow Services Ltd
Bank: HSBC Corporate London
IBAN: GB29HBUK40127684920192
SWIFT: HBUKGB41XXX
Reference: PROJECT-APEX-CLOSING-TRANCHE-1

Due to strict SEC disclosure restrictions, please do not discuss this transaction over Slack or email anyone else until the press release goes live this afternoon.

Confirm once the wire has been queued with the bank.

Best regards,

Richard Mercer
Chief Executive Officer | Mercer Technologies Corp
"""
    ),

    # Baseline Threat 3: Legitimate Workplace Email
    (
        "legitimate_workplace.eml",
        """Delivered-To: sarah.jenkins@corp.google.com
Received: by 2002:a05:6512:110:0:0:0:0 with SMTP id m10csp1928341;
        Mon, 15 Jan 2024 09:30:15 -0500 (EST)
Authentication-Results: mx.google.com;
       dkim=pass header.i=@google.com header.s=20230601;
       spf=pass smtp.mailfrom=engineering-updates@google.com;
       dmarc=pass (p=REJECT) header.from=google.com
Received: from mail-sor-f41.google.com (mail-sor-f41.google.com [209.85.220.41])
        by mx.google.com with ESMTP id d9si9182341plk.2.2024.01.15.09.30.14
        for <sarah.jenkins@corp.google.com>;
        Mon, 15 Jan 2024 09:30:14 -0500 (EST)
Received: from internal-ci.corp.google.com (10.12.0.4) by mail-sor-f41.google.com;
        Mon, 15 Jan 2024 09:30:10 -0500
Message-ID: <109283019283.engineering@google.com>
Date: Mon, 15 Jan 2024 09:30:10 -0500
From: "Google Engineering Updates" <engineering-updates@google.com>
To: sarah.jenkins@corp.google.com
Subject: Monthly Engineering Architecture & Security Summary - January 2024
Content-Type: text/plain; charset="UTF-8"

Hi Sarah,

Here is the monthly summary of our microservice infrastructure migration and security posture enhancements across all engineering teams.

Key progress:
1. Completed zero-trust microservice infrastructure boundary rollout.
2. Hardened authentication tokens and secrets rotation.
3. Updated CI/CD pipeline automated regression tests.

Best regards,
Engineering Operations Team
"""
    ),

    # Campaign 1: Operation GhostRelay (CMP-2024-0034) - Fictional Banking Credential Harvesting
    (
        "04_apex_kyc_escalation.eml",
        """From: Apex NetBanking Care <alerts@onlineapex-kyc-update.com>
To: victim.user@corporate.internal
Subject: Final Notice: Immediate Apex NetBanking Access Termination Warning
Date: Mon, 15 Jan 2024 11:15:00 +0000
Message-ID: <20240115111500.8372.qmail@onlineapex-kyc-update.com>
Received: from mx.corporate.internal (10.0.0.1) by mail.corporate.internal; Mon, 15 Jan 2024 11:15:05 +0000
Received: from relay01.f3netze.de (185.220.101.5) by mx.corporate.internal with ESMTP; Mon, 15 Jan 2024 11:15:02 +0000
Received: from authenticated-user (185.220.101.5) by relay01.f3netze.de; Mon, 15 Jan 2024 11:15:00 +0000
Authentication-Results: mx.corporate.internal; spf=softfail (sender IP 185.220.101.5); dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Apex National Bank Customer,</p>
<p>Your online netbanking privileges are scheduled for immediate suspension within 12 hours due to pending mandatory KYC documentation under Regulatory Mandate 2024.</p>
<p>Please update your identity records immediately via our secure server: <a href="http://apex-secureverify.com/portal/login">https://www.online.apexbank.internal/kyc-update</a></p>
<p>Failure to comply will result in permanent account freezing.</p>
"""
    ),
    (
        "05_apex_netbanking_token.eml",
        """From: Apex Security Desk <security@apex-netbanking-alert.xyz>
To: target.analyst@enterprise.com
Subject: Security Alert: High Value Transaction Authorization Required
Date: Mon, 15 Jan 2024 09:30:00 +0000
Message-ID: <20240115093000.91823.smtp@apex-netbanking-alert.xyz>
Received: from mx.enterprise.com (10.0.1.2) by internal.enterprise.com; Mon, 15 Jan 2024 09:30:08 +0000
Received: from mail.jonasbunde-vps.net (194.26.29.117) by mx.enterprise.com with ESMTP; Mon, 15 Jan 2024 09:30:04 +0000
Authentication-Results: mx.enterprise.com; spf=fail (IP 194.26.29.117); dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Apex Customer,</p>
<p>An outgoing fund transfer of $48,500.00 is currently pending your authorization token on device iPhone 14 Pro.</p>
<p>If you did not initiate this transfer, cancel the transaction immediately: <a href="http://apex-netbanking-alert.xyz/cancel-tx">https://netbanking.apexcommercial.internal/dispute</a></p>
"""
    ),
    (
        "06_apex_pan_link_phish.eml",
        """From: Apex Bank Alert <no-reply@apex-update-portal.com>
To: accounts.payable@victim-domain.internal
Subject: Mandatory Action: Apex Mobile Pay Account Verification
Date: Sun, 14 Jan 2024 16:45:00 +0000
Message-ID: <20240114164500.5512.mail@apex-update-portal.com>
Received: from mx1.victim-domain.internal (10.2.0.1) by mail.victim-domain.internal; Sun, 14 Jan 2024 16:45:06 +0000
Received: from tor-node-nl.f3netze.de (185.220.101.34) by mx1.victim-domain.internal with ESMTP; Sun, 14 Jan 2024 16:45:02 +0000
Authentication-Results: mx1.victim-domain.internal; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Valued Customer,</p>
<p>Link your tax ID to Apex Mobile NetBanking to maintain active debit card privileges before midnight.</p>
<p>Login securely: <a href="http://apex-update-portal.com/auth">https://online.apexbank.internal/login</a></p>
"""
    ),
    (
        "07_apex_statutory_directive.eml",
        """From: National Regulatory Compliance <circulars@regulatory-notice.internal>
To: compliance.officer@bank-entity.internal
Subject: STATUTORY ORDER: Mandatory Fraud Auditing of Dormant Beneficiaries
Date: Mon, 15 Jan 2024 08:00:00 +0000
Message-ID: <20240115080000.1102.qmail@regulatory-notice.internal>
Received: from mx.bank-entity.internal (10.0.0.5) by mail.bank-entity.internal; Mon, 15 Jan 2024 08:00:05 +0000
Received: from tor-exit-de.f3netze.de (185.220.102.8) by mx.bank-entity.internal with ESMTP; Mon, 15 Jan 2024 08:00:02 +0000
Authentication-Results: mx.bank-entity.internal; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>All scheduled commercial banks must review the attached statutory annexure and verify automated clearing portals immediately.</p>
<p>Access Directive Annexure: <a href="http://apex-secureverify.com/regulatory-directive">https://banking-regulator.internal/notifications/2024</a></p>
"""
    ),
    (
        "08_apex_reward_points_lure.eml",
        """From: Apex Card Rewards <rewards@onlineapex-kyc-update.com>
To: user.cardholder@corporatemail.internal
Subject: Congratulations! You have $985.00 Unclaimed Apex Reward Points Expiring Today
Date: Sun, 14 Jan 2024 19:20:00 +0000
Message-ID: <20240114192000.7812.smtp@onlineapex-kyc-update.com>
Received: from mx.corporatemail.internal (10.1.1.1) by mail.corporatemail.internal; Sun, 14 Jan 2024 19:20:04 +0000
Received: from tor-relay02.f3netze.de (185.220.101.9) by mx.corporatemail.internal with ESMTP; Sun, 14 Jan 2024 19:20:02 +0000
Authentication-Results: mx.corporatemail.internal; spf=softfail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Apex Cardholder,</p>
<p>Your accumulated 19,700 Apex Reward Points worth $985.00 are set to expire tonight. Redeem directly into your bank account:</p>
<p><a href="http://apex-secureverify.com/rewards/claim">https://online.apexbank.internal/redeem-now</a></p>
"""
    ),
    (
        "09_apex_credit_limit_scam.eml",
        """From: Apex Commercial Credit Division <limit-enhancement@apex-netbanking-alert.xyz>
To: premium.client@corporatemail.com
Subject: Instant Approval: Pre-Approved Credit Card Limit Enhancement to $100,000
Date: Mon, 15 Jan 2024 12:40:00 +0000
Message-ID: <20240115124000.3341.smtp@apex-netbanking-alert.xyz>
Received: from mx.corporatemail.com (10.0.0.2) by mail.corporatemail.com; Mon, 15 Jan 2024 12:40:06 +0000
Received: from vps-nl.jonasbunde-vps.net (194.26.29.120) by mx.corporatemail.com with ESMTP; Mon, 15 Jan 2024 12:40:03 +0000
Authentication-Results: mx.corporatemail.com; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Congratulations! You are eligible for an instant zero-fee credit limit increase to $100,000.</p>
<p>Claim pre-approved offer: <a href="http://apex-netbanking-alert.xyz/credit-boost">https://online.apexbank.internal/limit-upgrade</a></p>
"""
    ),
    (
        "10_apex_urgent_unblock.eml",
        """From: Apex Online Desk <alerts@apex-bank-verify.com>
To: customer.ops@enterprisemail.internal
Subject: Security Notice: Apex Internet Banking Account Temporarily Locked
Date: Mon, 15 Jan 2024 14:00:00 +0000
Message-ID: <20240115140000.9981.mail@apex-bank-verify.com>
Received: from mx.enterprisemail.internal (10.0.0.4) by mail.enterprisemail.internal; Mon, 15 Jan 2024 14:00:05 +0000
Received: from relay01.f3netze.de (185.220.101.5) by mx.enterprisemail.internal with ESMTP; Mon, 15 Jan 2024 14:00:02 +0000
Authentication-Results: mx.enterprisemail.internal; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html; charset="utf-8"

<p>Dear Customer, your Apex Bank internet banking ID has been temporarily locked after 3 failed password attempts.</p>
<p>Unlock your account now: <a href="http://apex-secureverify.com/apex/unlock">https://online.apexbank.internal/unlock</a></p>
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
    print(f"  [+] Created sanitized demo EML: {file_path}")

print(f"\n[OK] Materialized {len(emails)} sanitized demo EMLs across 3 campaign clusters (D4 / GAP-004).")
