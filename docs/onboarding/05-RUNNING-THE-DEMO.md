# 🖥️ 05 — RUNNING THE DEMO: The 5-Screen Presenter's Script & The 15-Critical Story

> *"A great demonstration is not a lecture about code. It is a live courtroom drama in five acts. Your role is not to explain every line of Python; your role is to walk the evaluators through an active investigation, let the machine prove its claims with live receipts, and tell the honest story of why our system looks alarming on purpose."*

---

## 🚦 Act 0: The One-Command Boot ("The Big Green Button")

### 💡 The Analogy
Starting a modern jet engine used to require flipping forty individual toggle switches across five cockpit panels. Modern airliners have a single automated push-button starter: the computer checks the fuel pumps, tests the igniters, spools the turbines, and confirms oil pressure automatically.

### 🛠️ In the Project
You do not need to open multiple terminal windows, run manual database scripts, or configure web servers. SENTRY boots with a single command:

```powershell
powershell -File tools/demo_day.ps1
```

* **What happens behind the scenes:** The script frees ports 8000 and 3000, initializes the local SQLite database, seeds the 📌 **18 demo emails**, boots the Python backend, launches the React frontend, and opens Google Chrome directly to the login screen.
* **Boot time:** Approximately 8 to 12 seconds.

> [!TIP]
> ### 🚑 The Emergency Reboot Path (If Anything Freezes)
> If a presenter accidentally closes the browser, hits the wrong key, or experiences a screen freeze, stay calm. Run this two-line emergency reset:
> ```powershell
> powershell -File tools/cleanup.ps1
> powershell -File tools/demo_day.ps1
> ```
> *What it does:* Cleans all ports, resets the database to the certified 18-email demo seed, and restores the live dashboard in under 15 seconds.

---

## 🔐 The Login Beat: "The Locked Workstation"

When Chrome opens, you will see a clean login dialog.

* 🗣️ **What to Say Aloud:**
  > *"Before we examine the threat feed, notice that SENTRY's workstation is locked by default. In a real Security Operations Center, chain of custody begins at authentication. An investigator must log in with audited credentials so that every subsequent forensic export carries an immutable digital signature. For our demonstration, the evaluation keys are pre-configured in our environment file."*

* 🖱️ **What to Do:**
  1. Click the pre-filled username (`analyst@sentry.internal`).
  2. Click the pre-filled password field (`SentryDemo2026!`).
  3. Click **Sign In**.

---

## 🖥️ Screen 1: The SOC Threat Dashboard & The 15-Critical Story

![SOC Threat Dashboard](../assets/tour/01-dashboard.png)
*Live visual from `docs/assets/tour/01-dashboard.png`: Metric summary cards (Total Emails: 18, Critical Threats: 15, High: 0, Medium: 1, Low: 2), category filter pills, and the real-time alert feed.*

### 🗣️ What to Say Aloud:
> *"We are looking at the Security Operations Center dashboard. Across the top, five live metric cards summarize the current organizational posture. Notice the first number: exactly 18 emails have been ingested into this workstation.*
> 
> *Now look at the red badge: 15 of those 18 emails are tagged CRITICAL.*
> 
> *When judges first see this screen, they often ask: 'Why are almost all of your demo emails red? Is your machine learning model over-sensitive?'*
> 
> *Here is the honest answer: This is an active incident investigation corpus. We did not load a company's routine spam folder filled with shoe advertisements. We loaded an active, coordinated phishing attack targeting Apex National Bank. 15 of these emails are red because they represent real, dangerous attacks—including 10 spoofed banking alerts, 3 executive impersonation letters, and 2 advance-fee fraud scams.*
> 
> *Our system is not trigger-happy; when we benchmarked this exact model against 6,777 legitimate corporate emails from the Enron corpus, SENTRY raised exactly zero false alarms. When an email is red here, it is because the evidence demanded it."*

* 🖱️ **What to Do:**
  1. Point your mouse cursor at the **18 Total Emails** card.
  2. Point at the **15 Critical Threats** card.
  3. Click on the first row in the alert feed: **"Urgent: Account Verification Required - Apex National Bank"** (Email ID `1`).

---

## 🔬 Screen 2: The Forensic Dissection Workbench

![Forensic Dissection Workbench](../assets/tour/02-forensic-analyzer.png)
*Live visual from `docs/assets/tour/02-forensic-analyzer.png`: Split-screen workbench showing the sanitized raw email payload on the left and tabbed forensic analysis on the right.*

### 🗣️ What to Say Aloud:
> *"Clicking an alert opens SENTRY's forensic workbench. Notice the split-screen layout:*
> 
> *On the left side is the preserved email payload. The visual text looks identical to what landed in the victim's inbox, but SENTRY has stripped all active tracking scripts using an automated safety wash. The analyst can inspect the attacker's words safely without risking their own workstation.*
> 
> *On the right side is the forensic dissection panel. SENTRY does not give a vague 'spam percentage.' It breaks the investigation into four transparent dimensions: Headers, Linguistic Analysis, Authentication, and Technical Indicators.*
> 
> *Notice the overall Threat Score: 0.94 CRITICAL. Next, we will look at the cryptographic evidence that drove this score."*

* 🖱️ **What to Do:**
  1. Gesture to the left panel (the banking alert letter).
  2. Gesture to the right panel (the 0.94 score and breakdown tabs).
  3. Click on the **Authentication** tab.

---

## 🛂 Screen 3: Authentication Forensics & The Bouncer Defense

![Authentication Forensics](../assets/tour/03-authentication-forensics.png)
*Live visual from `docs/assets/tour/03-authentication-forensics.png`: SPF / DKIM / DMARC cryptographic verdict matrix, origin geolocation, and authentication failure score elevation.*

### 🗣️ What to Say Aloud:
> *"This is the email's international passport check. SENTRY interrogates the three foundational email authentication protocols:*
> 
> *First, SPF: Did the sending server have permission from Apex National Bank? FAILED.*
> *Second, DKIM: Does the message carry the bank's genuine digital cryptographic signature? FAILED.*
> *Third, DMARC: What does the bank's official policy mandate? REJECT.*
> 
> *Because cryptographic authentication hard-failed, SENTRY enforced our second signature defense: The Honest Score Floor. Even if the text sounded calm, the threat score was automatically elevated to at least 0.85 by security policy—and both numbers are preserved in our audit log.*
> 
> *Furthermore, look at the origin IP address: 203.0.113.9. An attacker injected a fake internal loopback address (127.0.0.1) into the header chain to pretend the mail came from inside the building. SENTRY's Reserved-IP Bouncer recognized the deception, skipped the fake private address, and isolated the real external gateway on the public internet."*

* 🖱️ **What to Do:**
  1. Point to the red **FAIL** badges for SPF and DKIM.
  2. Point to the **Origin IP (203.0.113.9)** and country tag.
  3. Click on the **Relay Map** navigation tab on the top menu bar.

---

## 🗺️ Screen 4: The Global Hop Relay Map

![Global Relay Geolocation Map](../assets/tour/05-relay-map.png)
*Live visual from `docs/assets/tour/05-relay-map.png`: Multi-hop transmission route plotted across global coordinates, highlighting the originating network boundary.*

### 🗣️ What to Say Aloud:
> *"Here, SENTRY transforms hidden postal transit stamps into physical geography. Every server that forwarded this email stamped a hidden Received: header onto the letter.*
> 
> *SENTRY reads these stamps from bottom to top—like archaeological layers—and plots the physical journey of the packet across an interactive global map using completely local, offline geolocation databases.*
> 
> *We can see the packet enter the internet at an untrusted hosting provider overseas, bounce through an intermediate relay in Western Europe, and finally arrive at our corporate perimeter gateway. An investigator can see the entire travel itinerary in three seconds."*

* 🖱️ **What to Do:**
  1. Hover your mouse over the initial origin pin.
  2. Trace the curved polyline to the intermediate hop.
  3. Click on the **Campaign Graph** navigation tab on the top menu bar.

---

## 🕸️ Screen 5: The Campaign Knowledge Graph

![Multi-Entity Campaign Knowledge Graph](../assets/tour/06-campaign-graph.png)
*Live visual from `docs/assets/tour/06-campaign-graph.png`: Deterministic D3 force-directed network graph showing clustered threat campaigns, shared IP supernodes, and Gate 21 spacing clearance.*

### 🗣️ What to Say Aloud:
> *"This is SENTRY's campaign correlation engine—the detective's pinboard brought to life.*
> 
> *Standard security tools evaluate each email in complete isolation. SENTRY looks across the entire enterprise. It extracts sending domains, origin IP addresses, and reply mailboxes, linking them into an interactive network graph.*
> 
> *Notice this dense cluster on the left: five separate phishing emails sent to five different employees all connect to a single central supernode—the fraudulent domain apex-bank-security.com. SENTRY automatically grouped them into Campaign CAMP-APEX-FIN-01.*
> 
> *Notice our third signature defense: The Self-Spoof Refusal. Because this email spoofed our internal domain, SENTRY extracted the attacker's real external IP address for firewall blocking, but strictly refused to blacklist apexbank.com—preventing our own corporate email from being accidentally taken offline.*
> 
> *Finally, notice the layout itself: every node maintains a minimum distance of at least 26 pixels from its neighbors. In Gate 21 of our verification harness, we mathematically test this canvas so nodes never overlap or become unreadable during a live investigation."*

* 🖱️ **What to Do:**
  1. Click on the central domain supernode (`apex-bank-security.com`).
  2. Drag the cluster gently with your mouse to demonstrate live D3 force physics.
  3. Click the **Export Dossier** button in the top right corner.

---

## 📄 The Grand Finale: The Court-Admissible Dossier Export

![Court-Admissible Forensic PDF Report](../assets/tour/08-forensic-report.png)
*Live visual from `docs/assets/tour/08-forensic-report.png`: The court-ready PDF dossier layout featuring executive summary, monospace Courier hashes, and the complete 4-row IOC table.*

### 🗣️ What to Say Aloud:
> *"Finally, when the investigation concludes, SENTRY compiles the entire evidentiary record into a court-admissible PDF dossier adhering to international RFC 3227 standards.*
> 
> *Every cryptographic SHA-256 fingerprint is printed in fixed-width monospace Courier font to prevent visual truncation in legal exhibits. Every action carries an RFC 3339 universal millisecond timestamp.*
> 
> *And here at the bottom is our standardized 4-Row IOC Table: the malicious origin IP, the forged sender domain, the trap reply-to address, and the trap reply-to domain—giving network administrators exact technical coordinates to update firewalls in sixty seconds.*
> 
> *This is SENTRY: from the initial crime scene to the judge's courtroom bench, evidence that is complete, truthful, and tamper-proof."*

---

## 🛑 The Never-Say List: Presenter Guidelines

To maintain absolute credibility and protect yourself during judge Q&A, memorize these strict presentation boundaries:

| ❌ NEVER SAY THIS | ✅ SAY THIS INSTEAD | ⚠️ WHY (The Trap It Sets) |
|---|---|---|
| *"SENTRY uses advanced AI-powered algorithms..."* | *"SENTRY uses a 3-layer ensemble combining expert heuristics, statistical decision trees, and linguistic scoring."* | **The "AI" Trap:** Evaluators hate buzzwords. "AI" sounds like an ungrounded ChatGPT wrapper. Saying "calibrated machine learning and heuristics" proves you understand the underlying mathematics. |
| *"Our attention vectors detect urgency..."* | *"Our linguistic heuristic scoring evaluates urgency cues and financial pressure tokens."* | **The "Transformer" Trap:** "Attention" implies heavy Transformer/LLM models. SENTRY does not run PyTorch or HuggingFace in live production; it uses lightweight offline text scoring (<1ms). |
| *"SENTRY is 100% accurate and never makes mistakes."* | *"In benchmark testing on 15,240 historical emails, SENTRY achieved 0.961 accuracy, though partially in-sample. On 6,777 unseen legitimate emails, it achieved zero false positive elevations."* | **The "Perfection" Trap:** Experienced security judges know 100% accuracy is impossible. Admitting the in-sample limitation proves engineering honesty. |
| *"We are much better than commercial tools like Proofpoint or Microsoft Defender."* | *"SENTRY does not replace perimeter gateway filters; it operates as an investigative DFIR workbench when threats penetrate perimeter defenses."* | **The "Vendor" Trap:** Commercial vendors have billion-dollar budgets. Claiming to beat them invites hostile technical interrogation. SENTRY is a forensic workbench, not an email gateway. |
| *"We have over two hundred tests..."* | *"We have exactly 164 passing tests across 26 modules, verified by tools/validate_facts.py."* | **The "Invented Number" Trap:** Never approximate. Citing exact machine-verified numbers from `PROJECT_FACTS.md` demonstrates unyielding factual rigor. |

---

## 🎯 Station Checkpoint: The Spoken-Line Self-Test

Before moving to Station 06, practice saying these three answers aloud:

1. **How do you answer when a judge asks why 15 of 18 emails are CRITICAL?**
   * *Answer:* *"This is an active incident response corpus targeting Apex National Bank, not a general spam folder. All 15 red emails represent real, verified attacks. When tested against 6,777 legitimate emails, SENTRY produced zero false positive elevations."*
2. **How do you explain the 0.85 score floor in plain language?**
   * *Answer:* *"If an email's cryptographic passport completely fails, security policy mandates a minimum threat score of 0.85 (CRITICAL). However, SENTRY transparently preserves both the raw statistical score and the policy elevation on the report."*
3. **What is SENTRY's Self-Spoof Refusal?**
   * *Answer:* *"If an attacker spoofs our own corporate domain, SENTRY blocks the attacker's external IP address, but strictly refuses to blacklist our own domain, preventing self-inflicted corporate email shutdowns."*

---

## 🚪 Station Exit & Next Step

Now that you have mastered the live 5-screen demonstration script and the never-say guidelines, you are ready to arm yourself for the toughest part of any evaluation: **the 12 aggressive judge questions and the radical honesty posture.**

Proceed to: **[Station 06 — JUDGES AND QUESTIONS: The 12 Tough Inquiries & Defense Armor &rarr;](06-JUDGES-AND-QUESTIONS.md)**
