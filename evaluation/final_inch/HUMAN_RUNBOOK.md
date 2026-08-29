# SENTRY Post-Session Human Runbook (The Irreducible Remainder)

*Target Audience: Parth (Lead Presenter & Repository Owner)*  
*Scope: Physical actions, OAuth lifecycle revocation, UI media uploads, and in-person human usability interviews that cannot be executed autonomously by an agent.*

---

## Item 1: Token Revocation (Immediate Next Human Action)
> **Rationale:** All GitHub API operations (Branch Protection, Tag Rulesets, Metadata, Dependabot Alert Dismissals, PR Merges) are now 100% completed and sealed at `origin/main`. Revoking the stored session credential immediately terminates the active credential lifecycle and ensures zero latent access exposure.

**Exact Click-Path (~60 seconds):**
1. Open your browser and navigate to: [`https://github.com/settings/applications`](https://github.com/settings/applications) (or `Settings` $\rightarrow$ `Developer settings` $\rightarrow$ `Personal access tokens` / `Authorized OAuth Apps`).
2. Locate **Git Credential Manager** (or the specific OAuth/PAT entry used by the local CLI).
3. Click **Revoke** $\rightarrow$ Confirm **"I understand, revoke access"**.

---

## Item 2: Account Security Log Audit (Explicit Dated Verification)
> **Rationale:** Explicitly verify account-level security events to confirm no anomalous API or credential activities occurred.

**Exact Audit Steps:**
1. Navigate to: [`https://github.com/settings/security-log`](https://github.com/settings/security-log).
2. Filter / Review events dated **2026-08-29**.
3. Confirm all logged actions (`repo.update`, `ruleset.create`, `pull_request.merge`, `oauth_access.revoke`) match the documented actions in this report.
4. Confirm zero unauthorized IP addresses or unexpected geographic access points.

---

## Item 3: Fresh Credential Re-Authentication & Invariant Verification
> **Rationale:** Confirms that the old token transitions immediately to DEAD and establishes a fresh, clean credential state for local development.

**Exact Terminal Command:**
```bash
# 1. Trigger fresh OAuth browser flow
git fetch origin

# 2. Complete the browser-prompted authentication flow
```
*Note: Once re-authenticated, the agent can verify the live transition receipt on demand.*

---

## Item 4: Social Preview Image Upload
> **Rationale:** GitHub provides no public REST API endpoint for uploading repository social preview images (`og:image`); this is strictly a browser UI action.

**Exact Click-Path (~30 seconds):**
1. Navigate to: [`https://github.com/Parth-tab/SENTRY-AI-Powered-Email-Threat-Detection/settings`](https://github.com/Parth-tab/SENTRY-AI-Powered-Email-Threat-Detection/settings)
2. Scroll to the **"Social preview"** section (under General Settings).
3. Click **"Edit"** $\rightarrow$ **"Upload an image..."**.
4. Select file from disk: [`docs/assets/tour/05-relay-map.png`](file:///E:/SENTRY/docs/assets/tour/05-relay-map.png) (or [`docs/assets/dashboard.png`](file:///E:/SENTRY/docs/assets/dashboard.png)).
5. Click **Save Changes**.

---

## Item 5: Stranger Usability Interviews
> **Rationale:** Conduct three 2-minute silent observation evaluations with first-time viewers to gauge strangers' immediate mental model and capture unfiltered friction points.

**Instructions:**
1. Follow the protocol defined in [`evaluation/final_inch/STRANGER_PROTOCOL.md`](file:///E:/SENTRY/evaluation/final_inch/STRANGER_PROTOCOL.md).
2. Present `https://github.com/Parth-tab/SENTRY-AI-Powered-Email-Threat-Detection`.
3. Ask verbatim: *"Here's a thing I built — can you look at this page for two minutes and tell me what you think it is?"*
4. Record verbatim first sentence and debrief answers in [`evaluation/final_inch/stranger_results_template.md`](file:///E:/SENTRY/evaluation/final_inch/stranger_results_template.md).

---

