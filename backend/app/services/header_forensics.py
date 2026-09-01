import re
import ipaddress
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime
from typing import Dict, Any, List, Optional, Tuple

class HeaderForensicsService:
    # Regex patterns for Received header parsing
    RECEIVED_REGEXES = [
        # Standard: from host (ip) by host with proto id x for y; date
        re.compile(
            r'from\s+(?P<from_host>[^\s\(\)]+)?\s*(?:\((?:[^\)]*?\[)?(?P<from_ip>[0-9a-fA-F\:\.]+)[\]\)]*)?'
            r'\s+by\s+(?P<by_host>[^\s\(\)]+)'
            r'(?:\s+with\s+(?P<protocol>[^\s;]+))?'
            r'(?:[^\;]*?;\s*(?P<date>.*))?$',
            re.IGNORECASE | re.DOTALL
        ),
        # Variant with 'from [ip]' directly
        re.compile(
            r'from\s+\[(?P<from_ip>[0-9a-fA-F\:\.]+)\]\s+by\s+(?P<by_host>[^\s\(\)]+)'
            r'(?:\s+with\s+(?P<protocol>[^\s;]+))?'
            r'(?:[^\;]*?;\s*(?P<date>.*))?$',
            re.IGNORECASE | re.DOTALL
        ),
        # Fallback IP extractor anywhere in Received string
        re.compile(r'\[(?P<from_ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3}|[0-9a-fA-F:]{3,39})\]')
    ]

    @staticmethod
    def is_private_ip(ip_str: str) -> bool:
        """Determines if an IP is private, loopback, link-local, or non-routable special-use space."""
        from app.services.geo_origin import GeoOriginService
        return GeoOriginService.is_reserved_or_special_use_ip(ip_str)

    @classmethod
    def parse_received_chain(cls, received_headers: List[str]) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], List[str]]:
        """
        Reconstructs the relay path chronologically (from sender to final destination).
        Received headers in standard emails are prepended at each hop, so
        index 0 is the LAST hop, and index -1 is the FIRST hop.
        """
        hops: List[Dict[str, Any]] = []
        anomalies: List[str] = []

        # Process in chronological order (bottom to top)
        chronological_headers = list(reversed(received_headers))
        hop_timestamps: List[Optional[datetime]] = []

        for idx, header_text in enumerate(chronological_headers):
            clean_text = " ".join(header_text.split())
            hop_data = {
                "hop_number": idx + 1,
                "raw": clean_text,
                "from_host": None,
                "from_ip": None,
                "by_host": None,
                "protocol": "SMTP",
                "timestamp": None,
                "parsed_date": None,
                "is_private": False,
                "is_reliable": True,
                "hop_type": "transit"
            }

            matched = False
            for pattern in cls.RECEIVED_REGEXES[:2]:
                m = pattern.search(clean_text)
                if m:
                    gd = m.groupdict()
                    hop_data["from_host"] = gd.get("from_host")
                    hop_data["from_ip"] = gd.get("from_ip")
                    hop_data["by_host"] = gd.get("by_host")
                    hop_data["protocol"] = gd.get("protocol") or "SMTP"
                    date_str = gd.get("date")
                    if date_str:
                        hop_data["timestamp"] = date_str.strip()
                        try:
                            hop_data["parsed_date"] = parsedate_to_datetime(date_str.strip())
                        except Exception:
                            pass
                    matched = True
                    break

            if not matched:
                # Fallback IP extraction
                ip_match = cls.RECEIVED_REGEXES[2].search(clean_text)
                if ip_match:
                    hop_data["from_ip"] = ip_match.group("from_ip")

            if hop_data["from_ip"]:
                hop_data["is_private"] = cls.is_private_ip(hop_data["from_ip"])
            else:
                hop_data["is_private"] = True

            hop_timestamps.append(hop_data["parsed_date"])
            hops.append(hop_data)

        # Check timestamp consistency across chronological hops
        for i in range(len(hops) - 1):
            t1 = hops[i]["parsed_date"]
            t2 = hops[i+1]["parsed_date"]
            if t1 and t2:
                try:
                    # Normalize timezone awareness to allow safe subtraction
                    if t1.tzinfo is not None and t2.tzinfo is None:
                        t2 = t2.replace(tzinfo=t1.tzinfo)
                    elif t1.tzinfo is None and t2.tzinfo is not None:
                        t1 = t1.replace(tzinfo=t2.tzinfo)
                    time_delta = (t2 - t1).total_seconds()
                    if time_delta < -300: # Hop received 5+ minutes before it was sent -> clock skew or forged hop
                        anomalies.append(f"impossible_timestamp_sequence_hop_{i+1}_to_{i+2}")
                        hops[i]["is_reliable"] = False
                except Exception:
                    pass

        # Identify earliest reliable public hop (first public IP in chronological chain)
        earliest_reliable_hop = None
        for hop in hops:
            if hop["from_ip"] and not hop["is_private"]:
                earliest_reliable_hop = hop
                hop["hop_type"] = "origin"
                break

        if not earliest_reliable_hop and hops:
            # If all are private or internal, take the first hop available
            earliest_reliable_hop = hops[0]

        return hops, earliest_reliable_hop, anomalies

    @classmethod
    def evaluate_authentication(cls, headers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses SPF, DKIM, and DMARC headers with RFC compliance and penalty scoring.
        """
        auth_results_header = str(headers.get("Authentication-Results", ""))
        received_spf = str(headers.get("Received-SPF", ""))
        dkim_sig = str(headers.get("DKIM-Signature", ""))
        dmarc_filter = str(headers.get("DMARC-Filter", ""))

        # 1. SPF Evaluation
        spf_res = "none"
        spf_detail = "No SPF record or header found"
        spf_score = 0

        combined_spf = f"{auth_results_header} {received_spf}".lower()
        if "spf=pass" in combined_spf or "pass (" in received_spf.lower():
            spf_res = "pass"
            spf_detail = "Sender IP authorized by domain SPF record"
            spf_score = 1
        elif "spf=softfail" in combined_spf or "softfail" in received_spf.lower():
            spf_res = "softfail"
            spf_detail = "Domain transitioning SPF; sender IP not fully authorized (~all)"
            spf_score = -1
        elif "spf=fail" in combined_spf or "fail (" in received_spf.lower() or "spf=hardfail" in combined_spf:
            spf_res = "fail"
            spf_detail = "Sender IP explicitly unauthorized by domain SPF record (-all)"
            spf_score = -2
        elif "spf=neutral" in combined_spf or "neutral" in received_spf.lower():
            spf_res = "neutral"
            spf_detail = "Domain SPF record explicitly makes no statement (?all)"
            spf_score = 0

        # 2. DKIM Evaluation
        dkim_res = "none"
        dkim_detail = "No DKIM signature found"
        dkim_score = 0

        combined_dkim = f"{auth_results_header} {dkim_sig}".lower()
        if "dkim=pass" in combined_dkim:
            dkim_res = "pass"
            dkim_detail = "Cryptographic signature verified against DNS public key"
            dkim_score = 1
        elif "dkim=fail" in combined_dkim or ("dkim-signature" in headers and "dkim=pass" not in auth_results_header):
            if dkim_sig and "dkim=fail" in auth_results_header:
                dkim_res = "fail"
                dkim_detail = "Cryptographic signature invalid or body hash mismatch"
                dkim_score = -2
            elif dkim_sig:
                dkim_res = "neutral"
                dkim_detail = "DKIM signature present, unverified locally"
                dkim_score = 0

        # 3. DMARC Evaluation
        dmarc_res = "none"
        dmarc_policy = "none"
        dmarc_alignment = "none"
        dmarc_detail = "No DMARC evaluation found"
        dmarc_score = 0

        combined_dmarc = f"{auth_results_header} {dmarc_filter}".lower()
        if "dmarc=pass" in combined_dmarc:
            dmarc_res = "pass"
            dmarc_policy = "reject" if "p=reject" in combined_dmarc else "none"
            dmarc_alignment = "pass"
            dmarc_detail = "DMARC policy verified; SPF/DKIM identifier aligned"
            dmarc_score = 2
        elif "dmarc=fail" in combined_dmarc:
            dmarc_res = "fail"
            dmarc_alignment = "fail"
            if "p=reject" in combined_dmarc or "action=reject" in combined_dmarc:
                dmarc_policy = "reject"
                dmarc_score = -3
                dmarc_detail = "DMARC alignment failed under p=reject policy (critical risk)"
            elif "p=quarantine" in combined_dmarc:
                dmarc_policy = "quarantine"
                dmarc_score = -3
                dmarc_detail = "DMARC alignment failed under p=quarantine policy"
            else:
                dmarc_policy = "none"
                dmarc_score = -2
                dmarc_detail = "DMARC alignment failed under monitoring policy p=none"

        total_auth_score = spf_score + dkim_score + dmarc_score

        return {
            "spf": {"result": spf_res, "detail": spf_detail, "score": spf_score},
            "dkim": {"result": dkim_res, "detail": dkim_detail, "score": dkim_score},
            "dmarc": {
                "result": dmarc_res,
                "policy": dmarc_policy,
                "alignment": dmarc_alignment,
                "detail": dmarc_detail,
                "score": dmarc_score
            },
            "total_auth_score": total_auth_score,
            "is_spoofed": (spf_res in ["fail", "softfail"] and dkim_res in ["fail", "none"] and dmarc_res == "fail")
        }

    @classmethod
    def detect_anomalies(cls, email_data: Dict[str, Any], earliest_hop: Optional[Dict[str, Any]]) -> List[str]:
        """
        Cross-examines header fields for deceptive indicators, domain mismatches,
        and impersonation artifacts.
        """
        anomalies: List[str] = []
        headers = email_data.get("headers", {})

        from_raw = email_data.get("from_raw", "")
        sender_email = email_data.get("sender", "")
        sender_domain = email_data.get("sender_domain", "")

        # 1. Display Name Impersonation
        # Check if the display name contains an email or brand that doesn't match the actual sender domain
        display_name, _ = parseaddr(from_raw)
        if "@" in display_name:
            inner_email = re.search(r'[\w\.-]+@[\w\.-]+', display_name)
            if inner_email and inner_email.group(0).lower() != sender_email.lower():
                anomalies.append("display_name_contains_fake_email")
        
        # Check for Executive title spoofing from free email services (BEC indicator)
        exec_titles = ["ceo", "cfo", "coo", "chief", "president", "director", "executive", "officer", "vice president"]
        freemails = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "proton.me", "mail.com"]
        if any(title in display_name.lower() for title in exec_titles) and sender_domain in freemails:
            anomalies.append("freemail_executive_impersonation")

        # 2. Return-Path Mismatch
        return_path = str(headers.get("Return-Path", "")).strip("<>")
        if return_path and "@" in return_path:
            return_domain = return_path.split("@")[-1].lower()
            if sender_domain and return_domain != sender_domain:
                anomalies.append("return_path_domain_mismatch")

        # 3. Reply-To Mismatch
        reply_to = str(headers.get("Reply-To", "")).strip("<>")
        if reply_to and "@" in reply_to:
            _, reply_addr = parseaddr(reply_to)
            reply_domain = reply_addr.split("@")[-1].lower() if "@" in reply_addr else ""
            if sender_domain and reply_domain and reply_domain != sender_domain:
                anomalies.append("reply_to_domain_mismatch")

        # 4. Message-ID Domain Mismatch
        message_id = email_data.get("message_id", "")
        if "@" in message_id:
            msg_domain = message_id.split("@")[-1].strip(">").lower()
            # Allow common bulk delivery providers if legitimate, else flag
            common_providers = ["google.com", "protection.outlook.com", "amazonses.com", "sendgrid.net", "mailgun.org"]
            if sender_domain and msg_domain != sender_domain and not any(cp in msg_domain for cp in common_providers):
                anomalies.append("message_id_domain_mismatch")

        # 5. X-Originating-IP vs Earliest Hop Mismatch
        x_orig_ip = headers.get("X-Originating-IP") or headers.get("X-Sender-IP")
        if x_orig_ip and earliest_hop and earliest_hop.get("from_ip"):
            clean_x_ip = re.sub(r'[\[\]]', '', str(x_orig_ip)).strip()
            if clean_x_ip != earliest_hop["from_ip"] and not cls.is_private_ip(clean_x_ip):
                anomalies.append("x_originating_ip_discrepancy")

        # 6. Suspicious X-Mailer or User-Agent
        x_mailer = str(headers.get("X-Mailer", "") or headers.get("User-Agent", ""))
        suspicious_mailers = ["phpmailer", "massmailer", "directmail", "python", "curl", "sendblaster", "superspammer"]
        if any(sm in x_mailer.lower() for sm in suspicious_mailers):
            anomalies.append(f"suspicious_x_mailer_{x_mailer[:30]}")

        return anomalies
