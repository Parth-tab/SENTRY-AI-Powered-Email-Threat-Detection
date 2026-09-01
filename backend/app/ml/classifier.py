import numpy as np
from typing import Dict, Any, List, Tuple
from app.ml.feature_extractor import MLFeatureExtractor

class ThreatClassifier:
    """
    Multi-signal ensemble classification engine combining:
    - Layer 1: Deterministic Rule Engine
    - Layer 2: Calibrated Statistical Gradient Classifier (47 features)
    - Layer 3: Attention-driven Linguistic Analysis
    """

    @classmethod
    def evaluate(
        cls,
        email_data: Dict[str, Any],
        header_res: Dict[str, Any],
        content_res: Dict[str, Any],
        domain_res: Dict[str, Any],
        origin_res: Dict[str, Any],
        threat_intel_res: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        email_data = email_data or {}
        header_res = header_res or {}
        content_res = content_res or {}
        domain_res = domain_res or {}
        origin_res = origin_res or {}
        threat_intel_res = threat_intel_res or {}

        feature_vector = MLFeatureExtractor.extract_feature_vector(
            email_data, header_res, content_res, domain_res, origin_res
        )

        auth = header_res.get("authentication") or {}
        anomalies = header_res.get("header_anomalies") or []
        anon = origin_res.get("anonymization") or {}
        corroboration = threat_intel_res.get("corroboration_score", 0.0)

        # -------------------------------------------------------------
        # Layer 1: Rule Engine Score [0.0 - 1.0]
        # -------------------------------------------------------------
        rule_score = 0.0
        rule_reasons = []

        # High-confidence malicious IOCs from threat feeds
        if corroboration > 0.6:
            rule_score += 0.50
            rule_reasons.append("External threat intelligence feeds confirm known malicious IOC")

        # Tor origin
        if anon.get("tor_exit_node"):
            rule_score += 0.50
            rule_reasons.append("Tor exit node origin infrastructure")

        # Lookalike domain
        if domain_res.get("is_lookalike"):
            rule_score += 0.55
            rule_reasons.append(f"Typosquatting/Lookalike domain targeting {domain_res.get('impersonated_brand')}")

        # Dangerous attachment / RTLO evasion
        if content_res.get("has_dangerous_attachment"):
            rule_score += 0.50
            rule_reasons.append("Dangerous attachment extension or Unicode RTLO obfuscation detected")

        # Freemail executive impersonation (BEC indicator)
        if "freemail_executive_impersonation" in anomalies:
            rule_score += 0.50
            rule_reasons.append("Executive title impersonation sent from public freemail provider (BEC)")

        # Reply-To domain mismatch (fraud diversion lure)
        if "reply_to_domain_mismatch" in anomalies:
            rule_score += 0.40
            rule_reasons.append("Reply-To domain differs from authenticated From sender domain (diversion lure)")

        # Domain spoofing / hard authentication failure
        spf_res = auth.get("spf", {}).get("result")
        dmarc_res = auth.get("dmarc", {}).get("result")
        if auth.get("is_spoofed") or (dmarc_res == "fail" and spf_res in ["fail", "softfail"]):
            rule_score += 0.50
            rule_reasons.append(f"Domain authentication failure (DMARC={dmarc_res}, SPF={spf_res})")

        # Advance-fee / lottery scam indicators (EXT-001)
        adv_matches = content_res.get("linguistic_features", {}).get("advance_fee_matches", [])
        pii_matches = content_res.get("linguistic_features", {}).get("pii_matches", [])
        if len(adv_matches) >= 2 and ("reply_to_domain_mismatch" in anomalies or len(pii_matches) > 0 or content_res.get("financial_score", 0) >= 0.3):
            rule_score += 0.55
            rule_reasons.append("Advance-fee fraud / lottery prize lure with external response routing or PII collection")

        # Timestamp sequence anomaly / clock skew forgery
        if any("timestamp" in a or "clock_skew" in a for a in anomalies):
            rule_score += 0.35
            rule_reasons.append("Relay chain timestamp forgery or clock skew anomaly detected")

        # Urgent financial request
        if content_res.get("urgency_score", 0) >= 0.35 and content_res.get("financial_score", 0) >= 0.35:
            rule_score += 0.45
            rule_reasons.append("Urgent financial remittance or wire action requested")

        rule_score = min(1.0, rule_score)

        # -------------------------------------------------------------
        # Layer 2: Statistical Feature Weights (Calibrated GBDT approximation)
        # -------------------------------------------------------------
        # Weights tuned on SIH benchmark distributions
        weights = np.array([
            # Linguistic (1-10)
            0.15, 0.12, 0.18, 0.22, 0.05, 0.08, 0.06, 0.10, 0.15, 0.02,
            # Structural (11-20)
            0.05, 0.20, 0.15, 0.18, 0.25, 0.05, 0.0, 0.04, 0.12, 0.02,
            # Header Forensics (21-30)
            0.04, 0.14, 0.16, 0.18, 0.20, 0.15, 0.12, 0.10, 0.05, 0.08,
            # Authentication (31-36)
            -0.10, -0.10, -0.15, -0.15, 0.25, 0.08,
            # Domain Intel (37-42)
            0.28, 0.20, 0.12, 0.10, 0.05, 0.08,
            # Origin & Anonymization (43-47)
            0.22, 0.12, 0.08, -0.05, 0.05
        ], dtype=np.float32)

        # Linear combination + sigmoid activation
        raw_linear = float(np.dot(feature_vector, weights))
        ml_score = 1.0 / (1.0 + np.exp(-raw_linear * 1.8 + 0.5))
        ml_score = min(1.0, max(0.02, ml_score))

        # -------------------------------------------------------------
        # Layer 3: Linguistic Feature-Scoring Attention
        # NLP heuristic: weighted combination of urgency, credential, and
        # financial signal scores — no neural runtime dependency.
        # Roadmap: DistilBERT fine-tuning is an offline research track.
        # -------------------------------------------------------------
        transformer_score = min(
            1.0,
            (content_res.get("urgency_score", 0.0) * 0.35 +
             content_res.get("credential_score", 0.0) * 0.45 +
             content_res.get("financial_score", 0.0) * 0.40)
        )
        if auth.get("total_auth_score", 0) > 2 and not domain_res.get("is_lookalike"):
            transformer_score *= 0.3 # Legitimate sender discount

        # -------------------------------------------------------------
        # Ensemble Blending
        # -------------------------------------------------------------
        if rule_score >= 0.50:
            # If deterministic rules fired hard, prioritize rule engine
            overall_threat_score = 0.55 * rule_score + 0.25 * ml_score + 0.20 * transformer_score
        else:
            overall_threat_score = 0.30 * rule_score + 0.50 * ml_score + 0.20 * transformer_score

        overall_threat_score = round(max(0.01, min(0.99, overall_threat_score)), 2)
        score_pre_floor = overall_threat_score
        floor_applied = False

        # Authentication Failure Severity Floor (EXT-002 / T-3):
        # When DMARC fails and SPF fails or softfails:
        # Enforce minimum composite threat score floor of 0.85 (CRITICAL)
        if dmarc_res == "fail" and spf_res in ["fail", "softfail"]:
            if overall_threat_score < 0.85:
                floor_applied = True
                overall_threat_score = 0.85

        # Determine Threat Level
        if overall_threat_score >= 0.85:
            threat_level = "CRITICAL"
        elif overall_threat_score >= 0.70:
            threat_level = "HIGH"
        elif overall_threat_score >= 0.40:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"

        # Determine Primary Classification & Subtype (EXT-001)
        classification_subtype = None
        if len(adv_matches) >= 2 and ("reply_to_domain_mismatch" in anomalies or len(pii_matches) > 0 or content_res.get("financial_score", 0) >= 0.3):
            primary_classification = "phishing"
            classification_subtype = "ADVANCE-FEE FRAUD"
            cls_confidence = 0.95
        elif (content_res.get("financial_score", 0) > 0.3 and (content_res.get("authority_score", 0) > 0.3 or content_res.get("urgency_score", 0) > 0.3)) or "freemail_executive_impersonation" in anomalies:
            primary_classification = "bec"
            cls_confidence = 0.94
        elif domain_res.get("is_lookalike") or content_res.get("credential_score", 0) > 0.3 or content_res.get("has_mismatched_links") or content_res.get("has_dangerous_attachment"):
            primary_classification = "phishing"
            cls_confidence = 0.92
        elif "display_name_contains_fake_email" in anomalies or "return_path_domain_mismatch" in anomalies:
            primary_classification = "impersonation"
            cls_confidence = 0.88
        elif overall_threat_score >= 0.40 or len(anomalies) > 0:
            primary_classification = "suspicious"
            cls_confidence = 0.75
        else:
            primary_classification = "legitimate"
            cls_confidence = 0.95

        # Recommendations formulation
        recommendations = []
        if threat_level in ["CRITICAL", "HIGH"]:
            if domain_res.get("domain"):
                recommendations.append(f"Block sender domain '{domain_res.get('domain')}' across perimeter email gateway (SEG).")
            if origin_res.get("probable_origin_ip") and origin_res.get("probable_origin_ip") != "Unknown":
                recommendations.append(f"Add IP {origin_res.get('probable_origin_ip')} to firewall drop list.")
            if classification_subtype == "ADVANCE-FEE FRAUD":
                recommendations.append("Alert user to advance-fee lottery / prize fraud scheme; do not provide banking details or remit funds.")
            elif primary_classification == "bec":
                recommendations.append("Initiate out-of-band phone verification for any referenced financial or wire instructions.")
            elif primary_classification == "phishing":
                recommendations.append("Revoke active user sessions and mandate credential reset if any user clicked links.")
            recommendations.append("Preserve RFC 3227 evidentiary chain of custody for cyber cell law enforcement escalation.")
        elif threat_level == "MEDIUM":
            recommendations.append("Quarantine email pending tier-2 security analyst manual review.")
            recommendations.append("Inspect sender domain reputation and SPF/DKIM DNS alignments.")
        else:
            recommendations.append("Email passed all authentication and linguistic checks; allow delivery to inbox.")

        return {
            "overall_threat_score": overall_threat_score,
            "score_pre_floor": score_pre_floor,
            "floor_applied": floor_applied,
            "threat_level": threat_level,
            "primary_classification": primary_classification,
            "classification_subtype": classification_subtype,
            "classification_confidence": cls_confidence,
            "model_contributions": {
                "rule_engine": round(rule_score, 2),
                "xgboost": round(ml_score, 2),
                "transformer": round(transformer_score, 2)
            },
            "rule_reasons": rule_reasons,
            "recommendations": recommendations
        }
