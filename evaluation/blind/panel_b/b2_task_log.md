# B2 Hostile SOC Analyst Task Log

### Task 1: An email just arrived. Is it dangerous? Tell me why.
- **Outcome**: SUCCESS
- **Clicks**: 1
- **Hesitation / Friction**: None — Investigate button opens modal immediately.
- **Explanation to Boss**: "Yes, it is classified as CRITICAL (score 0.94) because the authentication checks (SPF/DKIM/DMARC) failed and the linguistic attention detected high urgency financial credential harvesting."

### Task 2: Prove to me where it physically came from.
- **Outcome**: FAIL
- **Clicks**: 1
- **Hesitation / Friction**: Origin card is on right pane of modal; requires scrolling on smaller screens.
- **Explanation to Boss**: "The header hops trace back through relays to an earliest reliable IP in Moscow, Russia (ASN 49505), with an active Tor exit node anonymization flag."

### Task 3: Show me it's connected to other emails.
- **Outcome**: SUCCESS
- **Clicks**: 2
- **Hesitation / Friction**: Graph canvas displays nodes and cluster sidebar; clicking a node requires precise cursor targeting.
- **Explanation to Boss**: "The Campaign Graph links this email via shared domain infrastructure and sender IP cluster to 4 other phishing incidents across the organization."

### Task 4: Give me one artifact I could hand to the police.
- **Outcome**: SUCCESS
- **Clicks**: 1
- **Hesitation / Friction**: None — 'Export Court-Admissible PDF' button is clearly visible.
- **Explanation to Boss**: "We have an RFC 3227-compliant forensic PDF report with SHA-256 hash chains, raw headers, and custody ledger ready for law enforcement submission."

### Task 5: Prove the evidence hasn't been tampered with.
- **Outcome**: SUCCESS
- **Clicks**: 1
- **Hesitation / Friction**: Need to understand that COC ID and SHA-256 hash in the report viewer form the tamper-evident chain.
- **Explanation to Boss**: "Every ingested byte is bound to an immutable SHA-256 hash recorded in the evidence vault with timestamps and sequential hash chaining."

