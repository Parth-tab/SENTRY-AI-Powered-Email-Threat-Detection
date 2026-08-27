import numpy as np
from typing import Dict, Any, List

class MLFeatureExtractor:
    FEATURE_NAMES = [
        # Linguistic (1-10)
        "urgency_score", "authority_score", "financial_score", "credential_score", "generic_greeting_count",
        "urgency_kw_count", "authority_kw_count", "financial_kw_count", "credential_kw_count", "body_length_log",
        # Structural (11-20)
        "url_count", "has_mismatched_links", "has_html_form", "has_password_input", "has_dangerous_attachment",
        "attachment_count", "image_to_text_ratio", "external_links_ratio", "suspicious_path_patterns", "raw_html_flag",
        # Header Forensics (21-30)
        "relay_hops_count", "impossible_timestamps", "display_name_fake_email", "return_path_mismatch",
        "reply_to_mismatch", "message_id_mismatch", "x_orig_ip_discrepancy", "suspicious_mailer", "missing_date_flag", "clock_skew_flag",
        # Authentication (31-36)
        "spf_score", "dkim_score", "dmarc_score", "total_auth_score", "is_spoofed_flag", "dmarc_reject_policy",
        # Domain Intel (37-42)
        "domain_is_lookalike", "domain_risk_score", "high_risk_tld_flag", "excessive_subdomains", "domain_age_risk", "mx_record_missing",
        # Origin & Anonymization (43-47)
        "is_tor_exit_node", "is_vpn_detected", "is_hosting_provider", "origin_confidence", "origin_country_risk"
    ]

    @classmethod
    def extract_feature_vector(cls, email_data: Dict[str, Any], header_res: Dict[str, Any], content_res: Dict[str, Any], domain_res: Dict[str, Any], origin_res: Dict[str, Any]) -> np.ndarray:
        """
        Extracts 47 engineered features into a normalized float array for ML inference.
        """
        feats = []

        # Linguistic (1-10)
        feats.append(float(content_res.get("urgency_score", 0.0)))
        feats.append(float(content_res.get("authority_score", 0.0)))
        feats.append(float(content_res.get("financial_score", 0.0)))
        feats.append(float(content_res.get("credential_score", 0.0)))
        ling = content_res.get("linguistic_features", {})
        feats.append(float(len(ling.get("generic_greetings", []))))
        feats.append(float(len(ling.get("urgency_keywords", []))))
        feats.append(float(len(ling.get("authority_references", []))))
        feats.append(float(len(ling.get("financial_requests", []))))
        feats.append(float(len(ling.get("credential_harvesting", []))))
        body_len = len(email_data.get("body_plain", ""))
        feats.append(float(np.log1p(body_len)))

        # Structural (11-20)
        feats.append(float(content_res.get("urls_count", 0)))
        feats.append(1.0 if content_res.get("has_mismatched_links") else 0.0)
        feats.append(1.0 if content_res.get("has_html_form") else 0.0)
        feats.append(1.0 if content_res.get("has_password_input") else 0.0)
        feats.append(1.0 if content_res.get("has_dangerous_attachment") else 0.0)
        feats.append(float(len(email_data.get("attachments", []))))
        feats.append(0.0) # image_to_text_ratio
        feats.append(1.0 if content_res.get("urls_count", 0) > 0 else 0.0)
        feats.append(1.0 if any("/login" in u.get("url", "") or "/verify" in u.get("url", "") for u in content_res.get("urls_found", [])) else 0.0)
        feats.append(1.0 if email_data.get("body_html") else 0.0)

        # Header Forensics (21-30)
        anomalies = header_res.get("header_anomalies", [])
        feats.append(float(header_res.get("relay_hops_count", 1)))
        feats.append(1.0 if any("impossible_timestamp" in a for a in anomalies) else 0.0)
        feats.append(1.0 if "display_name_contains_fake_email" in anomalies else 0.0)
        feats.append(1.0 if "return_path_domain_mismatch" in anomalies else 0.0)
        feats.append(1.0 if "reply_to_domain_mismatch" in anomalies else 0.0)
        feats.append(1.0 if "message_id_domain_mismatch" in anomalies else 0.0)
        feats.append(1.0 if "x_originating_ip_discrepancy" in anomalies else 0.0)
        feats.append(1.0 if any("suspicious_x_mailer" in a for a in anomalies) else 0.0)
        feats.append(0.0) # missing_date_flag
        feats.append(1.0 if not header_res.get("earliest_reliable_hop", {}).get("is_reliable", True) else 0.0)

        # Authentication (31-36)
        auth = header_res.get("authentication", {})
        spf = auth.get("spf", {})
        dkim = auth.get("dkim", {})
        dmarc = auth.get("dmarc", {})
        feats.append(float(spf.get("score", 0)))
        feats.append(float(dkim.get("score", 0)))
        feats.append(float(dmarc.get("score", 0)))
        feats.append(float(auth.get("total_auth_score", 0)))
        feats.append(1.0 if auth.get("is_spoofed") else 0.0)
        feats.append(1.0 if dmarc.get("policy") == "reject" else 0.0)

        # Domain Intel (37-42)
        feats.append(1.0 if domain_res.get("is_lookalike") else 0.0)
        feats.append(float(domain_res.get("risk_score", 0.0)))
        feats.append(1.0 if any("high_risk_tld" in f for f in domain_res.get("flags", [])) else 0.0)
        feats.append(1.0 if "excessive_subdomains" in domain_res.get("flags", []) else 0.0)
        feats.append(0.1) # domain_age_risk
        feats.append(0.0 if domain_res.get("mx_records_present", True) else 1.0)

        # Origin & Anonymization (43-47)
        anon = origin_res.get("anonymization", {})
        feats.append(1.0 if anon.get("tor_exit_node") else 0.0)
        feats.append(1.0 if anon.get("vpn_detected") else 0.0)
        feats.append(1.0 if anon.get("hosting_provider") else 0.0)
        feats.append(float(origin_res.get("confidence", 0.8)))
        feats.append(0.0) # origin country risk

        return np.array(feats, dtype=np.float32)
