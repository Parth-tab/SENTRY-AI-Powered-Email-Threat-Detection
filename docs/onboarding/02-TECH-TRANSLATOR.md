# 💡 02 — TECH TRANSLATOR: The 30 Core Terms Explained Through Real-Life Analogies

Welcome to **Station 02**. In the previous station, you learned the detective story behind SENTRY: treating emails like digital crime scenes.

Now, as you begin exploring how the machine works, you will encounter words that software engineers use every day. To a non-technical reader, these words can sound like a foreign language designed to confuse outsiders.

**This document is your universal translator.**

For every single term, you will find:
1. 💡 **Everyday Analogy:** A real-world parallel (kitchens, post offices, passports, courthouses).
2. 🔍 **Plain Definition:** The simplest possible explanation with zero buzzwords.
3. ⚖️ **In SENTRY:** Exactly how our software uses it.
4. 🧠 **Memory Hook:** A one-sentence phrase to lock it into your mind.
5. 🚪 **Where You'll Meet It Next:** The exact station in this guide where this term will appear.

---

## 🍽️ Cluster 1: The Web & How Programs Talk (Terms 1–6)

### 1. Server
* 💡 **The Analogy:** The kitchen, pantry, and dishwashing line of a 24-hour restaurant. You never see the cooks directly; they stay in the back preparing orders day and night.
* 🔍 **Plain Definition:** A dedicated computer that never sleeps, waiting to receive requests from other computers and deliver answers back.
* ⚖️ **In SENTRY:** The Python application running on port `8000` that inspects email headers, calculates threat scores, and builds PDF reports.
* 🧠 **Memory Hook:** *Servers serve; they do the heavy lifting in the back.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md), Station 03, where the server receives raw email bytes at the intake desk.

---

### 2. Client
* 💡 **The Analogy:** The diner sitting in a restaurant booth, reading the laminated menu and deciding what to eat.
* 🔍 **Plain Definition:** The visual program, phone app, or web browser that a human being interacts with directly.
* ⚖️ **In SENTRY:** The web browser running on port `3000` that displays the dark-themed analyst dashboard, maps, and network graphs.
* 🧠 **Memory Hook:** *Clients ask; servers answer.*
* 🚪 **Where You'll Meet It Next:** In [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md), where you will operate the client to show judges the 5 key screens.

---

### 3. Backend
* 💡 **The Analogy:** The engine block, pistons, spark plugs, and fuel pump hidden under the locked hood of a sports car.
* 🔍 **Plain Definition:** All the mathematical calculations, database queries, and behind-the-scenes logic that power an app out of human sight.
* ⚖️ **In SENTRY:** The 82 files in the `backend/` directory containing Python code for machine learning, forensic header parsing, and cryptographic checks.
* 🧠 **Memory Hook:** *Backend is the brain; frontend is the face.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), where we tour the 82 files in `backend/app/`.

---

### 4. Frontend
* 💡 **The Analogy:** The car's leather steering wheel, glowing speedometer, gas pedal, and touchscreen navigation display.
* 🔍 **Plain Definition:** Everything you can see, click, hover over, or type into on your computer screen.
* ⚖️ **In SENTRY:** The React and TypeScript code in `frontend/src/` that draws interactive severity badges, dynamic graph nodes, and map markers.
* 🧠 **Memory Hook:** *If your mouse can click it, it's frontend.*
* 🚪 **Where You'll Meet It Next:** In [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md), where you guide an evaluator across all 5 visual frontend panels.

---

### 5. API (Application Programming Interface)
* 💡 **The Analogy:** The restaurant waiter. You cannot walk into the kitchen and grab a steak off the grill yourself; you tell the waiter what you want, the waiter tells the chef in standard restaurant shorthand, and the waiter brings the finished plate back to your table.
* 🔍 **Plain Definition:** A formal, agreed-upon messenger system that lets two completely different computer programs communicate and exchange data securely.
* ⚖️ **In SENTRY:** The bridge connecting the React frontend to the Python backend. When you click an email in the list, the frontend sends an API request to the backend asking for that email's forensic report.
* 🧠 **Memory Hook:** *The messenger and order-taker between programs.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), when we inspect the 29 registered API doorways in `backend/app/api/`.

---

### 6. Endpoint
* 💡 **The Analogy:** A specific labeled counter at the post office: Window 1 is strictly for buying stamps; Window 2 is strictly for passport renewal; Window 3 is strictly for picking up registered parcels.
* 🔍 **Plain Definition:** A specific web address (URL) dedicated to performing one exact task and returning one exact type of data.
* ⚖️ **In SENTRY:** There are exactly 📌 `29 registered endpoints` (24 business forensic endpoints + 5 system health routes), such as `/api/v1/emails/` (to fetch the threat list) or `/api/v1/evidence/verify/1` (to verify an email's hash chain).
* 🧠 **Memory Hook:** *One specific doorway for one specific job.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md) and [04-FILE-TOUR.md](04-FILE-TOUR.md), where all 29 endpoints are verified by the fact validator.

---

## 🗄️ Cluster 2: Data & Quality Assurance (Terms 7–11)

### 7. Database
* 💡 **The Analogy:** A fireproof digital filing cabinet in the detective squad room, with indexed hanging folders, alphabetized dividers, and metal locks.
* 🔍 **Plain Definition:** A specialized program built to store, organize, search, and retrieve structured information permanently so it never vanishes when the power is turned off.
* ⚖️ **In SENTRY:** An SQLite database file (`backend/sentry.db`) storing the records of all 18 demo seed emails, threat scores, extracted IOCs, and hash chain blocks.
* 🧠 **Memory Hook:** *Where data sleeps safely between computer restarts.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md), when an incoming email is permanently recorded into the database vault.

---

### 8. Schema
* 💡 **The Analogy:** A rigid, pre-printed government customs declaration form. Box 1 must be your surname; Box 2 must be your birthdate; Box 3 must be your passport number. If you try to write a sentence in the birthdate box, the immigration officer immediately rejects the form.
* 🔍 **Plain Definition:** The blueprint or contract that strictly defines what fields, data types (numbers, words, dates), and structures a piece of data must have before software will accept it.
* ⚖️ **In SENTRY:** Pydantic schemas in `backend/app/schemas/` guaranteeing that every single analyzed email record always contains an email ID, a sender, a recipient, and a valid threat score between 0.0 and 1.0.
* 🧠 **Memory Hook:** *The rigid cookie-cutter that data must fit into.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), in the `backend/app/schemas/` tour table.

---

### 9. Test
* 💡 **The Analogy:** A pilot's laminated pre-flight checklist. Before a commercial airliner pushes back from the gate, the pilot checks the rudder, tests the fuel gauges, toggles the radios, and confirms the emergency oxygen pressure.
* 🔍 **Plain Definition:** A separate piece of code written to run the main software with known inputs and automatically verify that the output matches expectations 100%.
* ⚖️ **In SENTRY:** SENTRY possesses a comprehensive automated test battery containing 📌 `164 tests` across 26 test files in `backend/tests/`. Every single test passes before any change is allowed to ship.
* 🧠 **Memory Hook:** *Software checking software so humans don't have to guess.*
* 🚪 **Where You'll Meet It Next:** In [06-JUDGES-AND-QUESTIONS.md](06-JUDGES-AND-QUESTIONS.md), where judges ask: *"How do you know your system actually works?"*

---

### 10. Unit Test
* 💡 **The Analogy:** Testing a single brake pad on a workbench machine in the auto parts factory, completely detached from the car, to verify its friction coefficient before it is installed.
* 🔍 **Plain Definition:** A test that isolates a single, small function or calculation and checks whether it works correctly on its own, with zero external dependencies.
* ⚖️ **In SENTRY:** Testing just the IP address parser to confirm that an address like `127.0.0.1` is correctly recognized as private, without booting the database or web server.
* 🧠 **Memory Hook:** *Testing one single brick, not the whole building.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), touring `backend/tests/test_header_forensics.py`.

---

### 11. Gate / Harness
* 💡 **The Analogy:** An automated automotive crash-test facility. A robot launches the car down a track, smashes it into a concrete barrier at 60 km/h, checks whether the airbags deployed in under 30 milliseconds, and triggers an unyielding red alarm if the frame bends too much.
* 🔍 **Plain Definition:** An end-to-end robotic test rig that boots the entire system (backend, database, web browser, network connections), performs real human-like user actions, and certifies operational readiness.
* ⚖️ **In SENTRY:** `tools/verify_sentry.py` (The Golden Verification Harness). It runs exactly 📌 `21 sequential gates` (from Gate 1 booting the server to Gate 21 verifying graph cluster spacing). If even one gate fails, the build is rejected.
* 🧠 **Memory Hook:** *The unbribable electronic inspector.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md) (The Famous Files Spotlight) and [06-JUDGES-AND-QUESTIONS.md](06-JUDGES-AND-QUESTIONS.md).

---

## 📦 Cluster 3: Codebase & Team Collaboration (Terms 12–15, 18)

### 12. Repository (Repo)
* 💡 **The Analogy:** The master file cabinet and blueprint safe in an architect's office holding all drawings, permits, historical revisions, and engineer stamps for a skyscraper.
* 🔍 **Plain Definition:** The central folder containing all project code, documentation, test suites, assets, and its entire historical evolution.
* ⚖️ **In SENTRY:** The main folder on disk containing 📌 `551 tracked files`.
* 🧠 **Memory Hook:** *The project's permanent home address.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), as we walk through every room of the repository.

---

### 13. Git
* 💡 **The Analogy:** A video game save-point system that never overwrites old saves. You can travel back in time to Level 1, see exactly what choices you made, branch off into an alternate storyline, or return to your current progress whenever you like.
* 🔍 **Plain Definition:** A version control tool that records every single modification made to every file over time, tracking who made the change, when, and why.
* ⚖️ **In SENTRY:** The tool tracking all commits, tags, and branches, ensuring that every claim in our documentation matches our actual code history.
* 🧠 **Memory Hook:** *The time machine for software projects.*
* 🚪 **Where You'll Meet It Next:** In [06-JUDGES-AND-QUESTIONS.md](06-JUDGES-AND-QUESTIONS.md), under the immutable history discussion.

---

### 14. Branch
* 💡 **The Analogy:** A parallel drafting table where an author drafts an alternate chapter without touching or risking the published manuscript.
* 🔍 **Plain Definition:** An isolated copy of a codebase in Git where a developer can build a feature or fix a bug in complete safety without affecting the main product.
* ⚖️ **In SENTRY:** Feature branches like `feat/master-email-verification` or `docs/onboarding-guide`, which are only merged into the primary `main` branch after passing all tests.
* 🧠 **Memory Hook:** *A safe sandbox detour off the main highway.*
* 🚪 **Where You'll Meet It Next:** In [00-START-HERE.md](00-START-HERE.md), where we noted our branch governance rules.

---

### 15. Pull Request (PR)
* 💡 **The Analogy:** Submitting a newly written chapter to the editor-in-chief, complete with highlighted red-and-green edits and proofreader notes, requesting formal approval before it is printed in the newspaper.
* 🔍 **Plain Definition:** A formal proposal on GitHub to merge code from a feature branch into the main project, displaying every line changed and automated test results.
* ⚖️ **In SENTRY:** Every single enhancement to SENTRY—such as PR #14 (documentation unification), PR #15 (release v1.2.1), and PR #16 (master verification v1.2.2)—must be submitted as a PR and pass all automated tests before merging.
* 🧠 **Memory Hook:** *"Here is my proposed work — please inspect and merge."*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), in `.github/workflows/ci.yml`.

---

### 16. Continuous Integration (CI)
* 💡 **The Analogy:** An automated quality-control conveyor belt in a car factory. Every time a worker bolts a new part onto the chassis, robotic arms instantly scan the bolt tightness, check the paint thickness, and test electrical continuity before allowing the car down the line.
* 🔍 **Plain Definition:** An automated cloud robot that runs the entire test suite, code linters, and security checks every single time a developer saves or pushes code.
* ⚖️ **In SENTRY:** GitHub Actions runs 6 automated jobs across Python 3.11, Python 3.12, Node 18, and Node 20 on every push, ensuring that no broken code can ever slip into production.
* 🧠 **Memory Hook:** *The tireless robot that tests your work every time you save.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), examining `.github/workflows/ci.yml`.

---

## 🚢 Cluster 4: Packaging, Deployment & Cryptography (Terms 16–17, 19–21)

### 17. Container
* 💡 **The Analogy:** A standard steel shipping container loaded with a commercial printing press, its own diesel generator, power cables, and specific ink cartridges. Whether hoisted onto a freighter in Singapore or unloaded onto a flatbed in Rotterdam, the press operates identically the moment you start the generator.
* 🔍 **Plain Definition:** A lightweight, self-contained software package that bundles an application together with all the libraries, tools, and settings it needs to run, so it behaves identically on any computer.
* ⚖️ **In SENTRY:** SENTRY's backend and frontend are packaged into production containers, published on the GitHub Container Registry (`ghcr.io/parth-tab/sentry-backend:1.2.2`).
* 🧠 **Memory Hook:** *An entire application packed into an identical suitcase.*
* 🚪 **Where You'll Meet It Next:** In [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md), where container images are explained for enterprise deployment.

---

### 18. Docker
* 💡 **The Analogy:** The global port authority crane, tractor, and rail system that builds, lifts, transports, and manages those steel shipping containers worldwide.
* 🔍 **Plain Definition:** The software engine and platform used to build, share, and run containers on physical computers or cloud servers.
* ⚖️ **In SENTRY:** The `Dockerfile` and `docker-compose.yml` files that let anyone launch SENTRY with one command.
* 🧠 **Memory Hook:** *The engine that powers the container world.*
* 🚪 **Where You'll Meet It Next:** In [04-FILE-TOUR.md](04-FILE-TOUR.md), inspecting `backend/Dockerfile` and `frontend/Dockerfile`.

---

### 19. Deploy
* 💡 **The Analogy:** Unlocking the front glass doors, turning on the neon "OPEN" sign, and welcoming the public into a brand-new retail store on opening morning.
* 🔍 **Plain Definition:** The act of moving finished software from a developer's private laptop into a live operational environment where real users can log in and use it.
* ⚖️ **In SENTRY:** Running our automated boot script `tools/demo_day.ps1` or pulling live production images onto an enterprise server.
* 🧠 **Memory Hook:** *Flipping the switch from "under construction" to "live."*
* 🚪 **Where You'll Meet It Next:** In [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md), when we deploy the demo stack.

---

### 20. Hash
* 💡 **The Analogy:** A human fingerprint or barcode derived mathematically from physical skin ridges. No two people have the exact same fingerprint, and you cannot reconstruct a human being from their fingerprint alone.
* 🔍 **Plain Definition:** A mathematical calculation that converts any text, document, or file of any size into a fixed-length string of letters and numbers.
* ⚖️ **In SENTRY:** When an email arrives, SENTRY calculates its mathematical hash. Even if the email is 10 pages long, its hash is always an exact 64-character fingerprint.
* 🧠 **Memory Hook:** *One unique digital fingerprint for every document.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md), at the Evidence Intake Desk.

---

### 21. SHA-256
* 💡 **The Analogy:** A tamper-evident cryptographic wax seal: if even a single comma in a 500-page legal contract is modified, the seal shatters visibly and produces a totally different, unrecognizable fingerprint.
* 🔍 **Plain Definition:** A specific, military-grade hashing algorithm standardized by the US National Institute of Standards and Technology (NIST) that produces an unforgeable 64-character hexadecimal fingerprint.
* ⚖️ **In SENTRY:** Used to seal raw emails in the `evidence_vault/` and link each analysis step into a tamper-evident chain of custody.
* 🧠 **Memory Hook:** *The unbreakable gold standard of digital wax seals.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md) and [06-JUDGES-AND-QUESTIONS.md](06-JUDGES-AND-QUESTIONS.md), under legal admissibility.

---

## 🕵️ Cluster 5: The Threat & Forensic World (Terms 22–30)

### 22. DNS (Domain Name System)
* 💡 **The Analogy:** The contacts list in your smartphone. You don't memorize your mother's 10-digit telephone number; you tap "Mom," and your phone automatically looks up her number.
* 🔍 **Plain Definition:** The internet's global phonebook that translates human-friendly website names (like `apexbank.com`) into computer-routable IP numbers (like `203.0.113.9`).
* ⚖️ **In SENTRY:** When SENTRY investigates an email, it looks up the sender's domain name to find out what computers are officially authorized to send mail for that domain.
* 🧠 **Memory Hook:** *The internet's phonebook.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md), under Station 1 (Passport Control).

---

### 23. SPF / DKIM / DMARC
* 💡 **The Analogy:** The three anti-counterfeiting security features on an international passport:
  1. **SPF (Sender Policy Framework):** The embassy guest list ("Is the mail truck that brought this letter authorized by the bank?").
  2. **DKIM (DomainKeys Identified Mail):** The embassy's holographic wax seal ("Was the letter's text tampered with or modified in transit?").
  3. **DMARC (Domain-based Message Authentication, Reporting & Conformance):** The border guard's strict orders ("If the guest list or wax seal fails, reject the traveler at the border and alert the embassy!").
* 🔍 **Plain Definition:** The three industry-standard authentication checks that mathematically verify whether an email genuinely originated from the organization listed in the `From:` header.
* ⚖️ **In SENTRY:** Evaluated in Header Forensics. When an email fails authentication, SENTRY's policy raises its threat score to at least **0.85 (CRITICAL)**.
* 🧠 **Memory Hook:** *The digital passport and visa stamps of email.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md) and [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md) (Screen 3: Authentication Forensics).

---

### 24. Phishing
* 💡 **The Analogy:** An angler dangling a plastic worm on a sharp hook into dark water, hoping a fish mistakes the fake worm for food and bites down.
* 🔍 **Plain Definition:** A digital attack where an adversary poses as a trustworthy institution (a bank, hospital, or tech provider) to trick victims into revealing passwords or credit card numbers.
* ⚖️ **In SENTRY:** SENTRY's primary detection target, classified under the `PHISHING` threat category.
* 🧠 **Memory Hook:** *Fake bait designed to steal your credentials.*
* 🚪 **Where You'll Meet It Next:** In [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md), on the main threat dashboard.

---

### 25. Business Email Compromise (BEC)
* 💡 **The Analogy:** A con artist wearing an exact replica of the company CEO's three-piece suit walking quietly into the finance department and whispering: *"Wire $50,000 to this new vendor account immediately; it is a confidential acquisition."*
* 🔍 **Plain Definition:** A targeted spear-phishing attack that impersonates senior corporate executives or vendors to trick accounting staff into wiring money or changing bank details, usually containing zero malicious links or viruses.
* ⚖️ **In SENTRY:** Detected through linguistic analysis (identifying urgency and authority cues) and lookalike domain detection.
* 🧠 **Memory Hook:** *The corporate imposter whispering fraudulent wire instructions.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md), under Linguistic Profiling.

---

### 26. Advance-Fee Fraud (419)
* 💡 **The Analogy:** A stranger on a street corner whispering that they have an inheritance chest filled with $10 million in gold bullion, but they need you to lend them $500 right now for the customs padlock fee before they can split the fortune with you.
* 🔍 **Plain Definition:** A scam where the victim is promised a colossal financial windfall in exchange for paying a small upfront "clearance," "legal," or "handling" fee.
* ⚖️ **In SENTRY:** SENTRY includes a specialized detection subtype (`ADVANCE-FEE FRAUD`) tuned on historical Nigerian 419 archetypes.
* 🧠 **Memory Hook:** *Pay a small fee now to unlock a fortune that doesn't exist.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md) and `backend/tests/test_master_verification_email.py`.

---

### 27. Indicator of Compromise (IOC)
* 💡 **The Analogy:** The physical clues left behind at a crime scene: muddy boot prints by the back door, tire track impressions in the gravel, and a dropped matchbook with a bar logo.
* 🔍 **Plain Definition:** Technical artifacts left behind on a network or computer that positively identify malicious activity.
* ⚖️ **In SENTRY:** The standardized 4-row technical evidence table generated for every email: (1) Suspicious Sender IP, (2) Forged Sender Domain, (3) Trap Reply-To Address, and (4) Trap Reply-To Domain.
* 🧠 **Memory Hook:** *The digital clues left behind at the crime scene.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md) and [05-RUNNING-THE-DEMO.md](05-RUNNING-THE-DEMO.md) (The 4-Row IOC Table).

---

### 28. Forensic Chain of Custody
* 💡 **The Analogy:** The locked, signed paper log attached to a police evidence locker: Officer Smith logged the weapon at 10:15 AM; Lab Tech Jones checked it out at 11:30 AM; Ballistics Analyst Davis sealed it at 2:00 PM. If a single signature is missing or the date stamp is altered, the trial judge excludes the weapon from evidence.
* 🔍 **Plain Definition:** A chronological, tamper-evident record documenting the unbroken custody, inspection, and analysis of digital evidence to satisfy legal admissibility standards in court.
* ⚖️ **In SENTRY:** SENTRY implements RFC 3227 mathematical hash chains: every analysis step is permanently chained to the previous step using SHA-256 digests.
* 🧠 **Memory Hook:** *The legal diary proving evidence was never tampered with.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md) and [06-JUDGES-AND-QUESTIONS.md](06-JUDGES-AND-QUESTIONS.md).

---

### 29. Air-Gapped (Appliance)
* 💡 **The Analogy:** A nuclear submarine submerged beneath the polar ice cap: it has its own oxygen generators, nuclear power reactor, distilled water system, and navigation computers; it needs zero physical cables or radio signals connecting it to dry land.
* 🔍 **Plain Definition:** A computer system that is physically isolated from unsecured public networks and the internet to prevent eavesdropping or tampering.
* ⚖️ **In SENTRY:** SENTRY's certified appliance mode runs completely offline using local databases and bundled geographic tables, requiring zero internet access to perform full forensics.
* 🧠 **Memory Hook:** *Complete security through physical and digital isolation.*
* 🚪 **Where You'll Meet It Next:** In [06-JUDGES-AND-QUESTIONS.md](06-JUDGES-AND-QUESTIONS.md) (The Air-Gapped Defense).

---

### 30. Heuristic
* 💡 **The Analogy:** A seasoned nightclub bouncer scanning the queue outside the velvet rope: *"No steel-toed boots, valid photo ID required, no open drinks."* An instant, common-sense rule of thumb that weeds out 90% of troublemakers in 2 seconds without needing a background check.
* 🔍 **Plain Definition:** A practical, rule-based shortcut used to make fast, reliable decisions without needing complex mathematical calculations or neural networks.
* ⚖️ **In SENTRY:** Layer 1 of SENTRY's machine learning engine uses deterministic heuristics to catch known Tor exit nodes, forged sender names, and hard authentication failures in less than 1 millisecond.
* 🧠 **Memory Hook:** *A fast common-sense rule written by human experts.*
* 🚪 **Where You'll Meet It Next:** In [03-HOW-IT-WORKS.md](03-HOW-IT-WORKS.md), under The 3-Layer Machine Learning Ensemble.

---

## 🎯 Station Checkpoint: The 5-Minute Mastery Quiz

Test your memory before moving to Station 03:

1. **What is the difference between an API and an Endpoint?**
   * *Answer:* The API is the messenger (the waiter) that carries requests between two programs; the Endpoint is the specific door or service counter (Window 1 for mail, Window 2 for parcels) where one exact request is received.
2. **Why is SHA-256 called a "cryptographic wax seal" instead of just a summary?**
   * *Answer:* Because if even a single character or punctuation mark inside the document is changed, the SHA-256 seal shatters completely, generating an entirely different fingerprint and alerting investigators to tampering.
3. **What are the three security checks on an email's "passport," and what do they verify?**
   * *Answer:* SPF verifies the authorized guest list of mail trucks; DKIM verifies the sender's unforgeable signature; DMARC gives the border guard strict orders on whether to reject the email if either check fails.
4. **What is an IOC in SENTRY, and what 4 items does SENTRY always report?**
   * *Answer:* An Indicator of Compromise is technical evidence left behind by an attacker. SENTRY always reports: (1) Suspicious Sender IP, (2) Forged Sender Domain, (3) Trap Reply-To Address, and (4) Trap Reply-To Domain.
5. **Why can SENTRY run in an "air-gapped" room with zero internet connection?**
   * *Answer:* Because it is packaged as a self-contained appliance with local databases, bundled geolocation data, and offline heuristic analysis engines that do not depend on external cloud servers.

---

## 🚪 Station Exit & Next Step

Now that you speak the language of forensic cyber defense, you are ready to witness **one suspicious email travel through the entire SENTRY forensic crime lab**—from the moment it arrives at the intake desk to the moment its sealed evidence dossier is handed to a judge.

Proceed to: **[Station 03 — HOW IT WORKS: One Email's Journey Through the Crime Lab &rarr;](03-HOW-IT-WORKS.md)**
