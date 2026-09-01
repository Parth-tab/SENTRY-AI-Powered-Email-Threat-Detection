import re
import math
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

class ContentAnalysisService:
    # Linguistic keyword dictionaries
    URGENCY_KEYWORDS = [
        r"\b(?:immediately|urgent|urgently|within 24 hours|within 12 hours|final notice|account suspended|deactivated|action required|terminate|expires today|immediate response)\b"
    ]
    
    AUTHORITY_KEYWORDS = [
        r"\b(?:ceo|cfo|executive director|managing director|board of directors|it department|it support|security team|system administrator|compliance team|fraud department|chief executive)\b"
    ]
    
    FINANCIAL_KEYWORDS = [
        r"\b(?:wire transfer|bank details|update payment|invoice attached|remittance|swift code|bank account|routing number|gift card|payroll update|settlement|vendor payment|direct deposit)\b"
    ]
    
    CREDENTIAL_KEYWORDS = [
        r"\b(?:verify your account|confirm password|login to secure|update your kyc|kyc update|reset your credentials|unlock your account|validate your identity|security verification|re-authenticate)\b"
    ]
    
    GENERIC_GREETINGS = [
        r"\b(?:dear customer|dear user|dear client|dear member|dear account holder|dear sir/madam|undisclosed recipients)\b"
    ]

    ADVANCE_FEE_KEYWORDS = [
        r"\b(?:lottery(?:\s+winner|\s+draw|\s+promotion|\s+jackpot)?|lucky\s+winner|claim\s+your\s+prize|award\s+notification|processing\s+fee|advance\s+fee|claim\s+agent|beneficiary\s+(?:fund|payout|claim)|inheritance\s+(?:claim|fund)|grant\s+allocation|consignment\s+box|diplomatic\s+courier|unclaimed\s+(?:funds|assets))\b"
    ]

    PII_HARVESTING_KEYWORDS = [
        r"\b(?:passport(?:\s+copy|\s+number)?|national\s+id|driver'?s?\s+license|residential\s+address|date\s+of\s+birth|direct\s+telephone|bank\s+account\s+details|occupation|next\s+of\s+kin)\b"
    ]

    HIGH_RISK_EXTENSIONS = [".exe", ".scr", ".vbs", ".bat", ".ps1", ".iso", ".img", ".html", ".htm", ".docm", ".xlsm", ".js"]

    @classmethod
    def extract_urls(cls, body_plain: str, body_html: str) -> List[Dict[str, Any]]:
        """Extracts and analyzes all URLs, checking for text vs href mismatches."""
        urls: List[Dict[str, Any]] = []
        seen_urls = set()

        # 1. Parse HTML links for href vs text mismatch
        if body_html:
            a_tag_pattern = re.compile(r'<a\s+(?:[^>]*?\s+)?href=(["\'])(?P<href>[^"\']+)\1[^>]*>(?P<text>.*?)</a>', re.IGNORECASE | re.DOTALL)
            for m in a_tag_pattern.finditer(body_html):
                href = m.group("href").strip()
                text = re.sub(r'<[^>]+>', '', m.group("text")).strip()
                
                if not href.startswith(("http://", "https://")):
                    continue

                parsed_href = urlparse(href)
                href_domain = parsed_href.netloc.lower()
                
                is_mismatch = False
                # If anchor text looks like a URL but goes to a different domain
                if re.match(r'https?://[^\s]+', text, re.IGNORECASE):
                    parsed_text_url = urlparse(text)
                    text_domain = parsed_text_url.netloc.lower()
                    if text_domain and href_domain and text_domain != href_domain:
                        is_mismatch = True

                urls.append({
                    "url": href,
                    "domain": href_domain,
                    "display_text": text[:60] if text else href_domain,
                    "is_mismatch": is_mismatch,
                    "path": parsed_href.path
                })
                seen_urls.add(href)

        # 2. Extract plain text URLs
        raw_url_pattern = re.compile(r'https?://[^\s<>"\')]+', re.IGNORECASE)
        for m in raw_url_pattern.finditer(body_plain):
            url_str = m.group(0).rstrip(".,;")
            if url_str not in seen_urls:
                parsed = urlparse(url_str)
                urls.append({
                    "url": url_str,
                    "domain": parsed.netloc.lower(),
                    "display_text": parsed.netloc.lower(),
                    "is_mismatch": False,
                    "path": parsed.path
                })
                seen_urls.add(url_str)

        return urls

    @classmethod
    def analyze_content(cls, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts linguistic, structural, and behavioral features from email content.
        """
        # Unicode & Evasion Normalization (Neutralize Zero-Width, Homoglyphs & RTLO)
        import unicodedata
        
        raw_plain = email_data.get("body_plain", "")
        raw_subject = email_data.get("subject", "")
        has_rtlo = "\u202e" in raw_plain or "\u202e" in raw_subject or any("\u202e" in att.get("filename", "") for att in email_data.get("attachments", []))

        # Cyrillic to Latin homoglyph translation map for NLP extraction
        HOMOGLYPH_MAP = str.maketrans({
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x', 'і': 'i', 'ј': 'j', 'ѕ': 's',
            'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T',
            'Ү': 'Y', 'Х': 'X', 'І': 'I'
        })

        # Strip zero-width & invisible format characters
        cleaned_plain = re.sub(r'[\u200b\u200c\u200d\uFEFF\u200E\u200F\u202A-\u202E]', '', raw_plain)
        cleaned_subject = re.sub(r'[\u200b\u200c\u200d\uFEFF\u200E\u200F\u202A-\u202E]', '', raw_subject)

        # Normalize homoglyphs
        normalized_plain = cleaned_plain.translate(HOMOGLYPH_MAP)
        normalized_subject = cleaned_subject.translate(HOMOGLYPH_MAP)

        plain = normalized_plain.lower()
        html = email_data.get("body_html", "")
        subject = normalized_subject.lower()
        full_text = f"{subject}\n{plain}"

        # 1. Linguistic keyword matches
        urgency_matches = []
        for pat in cls.URGENCY_KEYWORDS:
            urgency_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        authority_matches = []
        for pat in cls.AUTHORITY_KEYWORDS:
            authority_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        financial_matches = []
        for pat in cls.FINANCIAL_KEYWORDS:
            financial_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        credential_matches = []
        for pat in cls.CREDENTIAL_KEYWORDS:
            credential_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        generic_matches = []
        for pat in cls.GENERIC_GREETINGS:
            generic_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        advance_fee_matches = []
        for pat in cls.ADVANCE_FEE_KEYWORDS:
            advance_fee_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        pii_matches = []
        for pat in cls.PII_HARVESTING_KEYWORDS:
            pii_matches.extend(re.findall(pat, full_text, re.IGNORECASE))

        # 2. Structural Features
        urls = cls.extract_urls(raw_plain, html)
        has_form = bool(re.search(r'<form\b', html, re.IGNORECASE)) if html else False
        has_password_input = bool(re.search(r'type=["\']password["\']', html, re.IGNORECASE)) if html else False
        has_mismatched_links = any(u.get("is_mismatch") for u in urls) or any("0x" in u.get("url", "") for u in urls)

        # Attachment checks
        attachments = email_data.get("attachments", [])
        has_dangerous_attachment = has_rtlo
        attachment_names = []
        for att in attachments:
            fname = att.get("filename", "").lower()
            attachment_names.append(fname)
            if any(fname.endswith(ext) for ext in cls.HIGH_RISK_EXTENSIONS) or "\u202e" in att.get("filename", ""):
                has_dangerous_attachment = True

        # Attention phrases for explainable UI highlights
        attention_tokens = list(set(
            urgency_matches + authority_matches + financial_matches + credential_matches + generic_matches + advance_fee_matches + pii_matches
        ))

        # 3. Calculate category signal scores [0.0 - 1.0]
        urgency_score = min(1.0, len(urgency_matches) * 0.35)
        authority_score = min(1.0, len(authority_matches) * 0.4)
        financial_score = min(1.0, len(financial_matches) * 0.4)
        credential_score = min(1.0, len(credential_matches) * 0.45)
        advance_fee_score = min(1.0, len(advance_fee_matches) * 0.40)
        pii_score = min(1.0, len(pii_matches) * 0.35)
        structural_risk_score = 0.0

        if has_mismatched_links:
            structural_risk_score += 0.4
        if has_form or has_password_input:
            structural_risk_score += 0.35
        if has_dangerous_attachment:
            structural_risk_score += 0.35
        structural_risk_score = min(1.0, structural_risk_score)

        # Determine primary action requested
        action_requested = "informational"
        if advance_fee_score > 0.3 or pii_score > 0.3:
            action_requested = "advance_fee_pii_solicitation"
        elif credential_score > 0.3:
            action_requested = "credential_verification"
        elif financial_score > 0.3:
            action_requested = "financial_transaction"
        elif urgency_score > 0.5:
            action_requested = "immediate_compliance"

        return {
            "urgency_score": round(urgency_score, 2),
            "authority_score": round(authority_score, 2),
            "financial_score": round(financial_score, 2),
            "credential_score": round(credential_score, 2),
            "advance_fee_score": round(advance_fee_score, 2),
            "pii_score": round(pii_score, 2),
            "structural_risk_score": round(structural_risk_score, 2),
            "action_requested": action_requested,
            "linguistic_features": {
                "urgency_keywords": list(set(urgency_matches)),
                "authority_references": list(set(authority_matches)),
                "financial_requests": list(set(financial_matches)),
                "credential_harvesting": list(set(credential_matches)),
                "generic_greetings": list(set(generic_matches)),
                "advance_fee_matches": list(set(advance_fee_matches)),
                "pii_matches": list(set(pii_matches))
            },
            "attention_tokens": attention_tokens[:15],
            "urls_found": urls,
            "urls_count": len(urls),
            "has_mismatched_links": has_mismatched_links,
            "has_html_form": has_form,
            "has_password_input": has_password_input,
            "has_dangerous_attachment": has_dangerous_attachment,
            "attachment_names": attachment_names
        }
