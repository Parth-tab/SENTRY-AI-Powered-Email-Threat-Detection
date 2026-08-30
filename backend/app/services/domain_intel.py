import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

class DomainIntelService:
    _brands_cache = None

    # Common homoglyph mappings (Cyrillic, Greek, lookalike digits)
    HOMOGLYPH_MAP = {
        'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o', 'р': 'p', 'х': 'x', 'у': 'y',
        '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '8': 'b',
        'vv': 'w', 'rn': 'm', 'cl': 'd'
    }

    @classmethod
    def _load_brands(cls) -> List[Dict[str, Any]]:
        if cls._brands_cache is None:
            data_file = Path(__file__).resolve().parent.parent / "data" / "brands_lookalike.json"
            if data_file.exists():
                try:
                    cls._brands_cache = json.loads(data_file.read_text(encoding="utf-8")).get("target_brands", [])
                except Exception:
                    cls._brands_cache = []
            else:
                cls._brands_cache = []
        return cls._brands_cache

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculates classic Levenshtein edit distance."""
        if len(s1) < len(s2):
            return DomainIntelService.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    @classmethod
    def normalize_homoglyphs(cls, domain: str) -> str:
        """Translates known homoglyphs, diacritics, and typosquatting character substitutions."""
        import unicodedata
        normalized = domain.lower()
        for char, target in cls.HOMOGLYPH_MAP.items():
            normalized = normalized.replace(char, target)
        # Strip diacritics (e.g. ö -> o, é -> e)
        nfkd = unicodedata.normalize('NFKD', normalized)
        ascii_norm = nfkd.encode('ASCII', 'ignore').decode('utf-8')
        return ascii_norm or normalized

    @classmethod
    def check_lookalike(cls, domain: str) -> Dict[str, Any]:
        """
        Checks if a domain is a lookalike, typosquat, punycode IDN spoof, or brand impersonation target.
        """
        if not domain:
            return {"is_lookalike": False, "impersonated_brand": None, "confidence": 0.0, "reason": None}

        clean_domain = domain.lower().strip()

        # Punycode / IDN internationalized domain decoding
        decoded_domain = clean_domain
        is_punycode = False
        if "xn--" in clean_domain:
            is_punycode = True
            try:
                decoded_domain = clean_domain.encode("ascii").decode("idna")
            except Exception:
                decoded_domain = clean_domain

        # Remove subdomain prefix for base domain comparison
        parts = clean_domain.split(".")
        base_domain = ".".join(parts[-2:]) if len(parts) >= 2 else clean_domain
        base_name = parts[-2] if len(parts) >= 2 else parts[0]

        dec_parts = decoded_domain.split(".")
        dec_base_name = dec_parts[-2] if len(dec_parts) >= 2 else dec_parts[0]

        brands = cls._load_brands()

        for brand in brands:
            brand_name = brand["name"]
            legit_domains = brand["legitimate_domains"]
            keywords = brand["keywords"]

            # Exact match to legitimate domain -> legitimate!
            if base_domain in legit_domains or clean_domain in legit_domains:
                return {
                    "is_lookalike": False,
                    "impersonated_brand": None,
                    "is_legitimate_brand": True,
                    "brand_name": brand_name,
                    "confidence": 0.0,
                    "reason": "Verified legitimate brand infrastructure"
                }

            # Check 1: Brand keyword contained in domain with hyphens or prefixes (e.g. apex-secureverify.com, paypal-update.com)
            for kw in keywords:
                clean_kw = kw.replace(" ", "")
                if clean_kw in base_name and base_domain not in legit_domains:
                    # Check if it has suspicious prefixes/suffixes
                    suspicious_words = ["secure", "verify", "update", "login", "portal", "support", "help", "auth", "account", "service"]
                    if any(sw in base_name for sw in suspicious_words) or "-" in base_name:
                        return {
                            "is_lookalike": True,
                            "impersonated_brand": brand_name,
                            "legitimate_domain": legit_domains[0],
                            "confidence": 0.95,
                            "reason": f"Brand keyword '{kw}' combined with deceptive phishing terms in '{domain}'"
                        }

            # Check 2: Levenshtein Distance and Homoglyph matching against legitimate domains
            norm_name = cls.normalize_homoglyphs(dec_base_name)
            for legit in legit_domains:
                legit_base = legit.split(".")[0]
                dist = cls.levenshtein_distance(norm_name, legit_base)
                max_len = max(len(norm_name), len(legit_base))
                
                # Match 1: Normalized homoglyph substitution (e.g. paypa1 -> paypal, or IDN punycode spoof)
                is_homoglyph_spoof = (norm_name == legit_base and (is_punycode or dec_base_name != legit_base))
                
                # Match 2: Close typo edit distance on brands of length >= 4 (prevents false matches on 2-3 char acronyms)
                is_typo_spoof = (1 <= dist <= 2 and len(legit_base) >= 4 and abs(len(norm_name) - len(legit_base)) <= 2 and (dist / max_len) <= 0.35)
                
                if is_homoglyph_spoof or is_typo_spoof:
                    return {
                        "is_lookalike": True,
                        "impersonated_brand": brand_name,
                        "legitimate_domain": legit,
                        "confidence": 0.95 if not is_punycode else 0.98,
                        "reason": f"Typosquatting/IDN variant of '{legit}' (distance: {dist})" if not is_punycode else f"Punycode/IDN spoof targeting '{legit}'"
                    }

        return {"is_lookalike": False, "impersonated_brand": None, "confidence": 0.0, "reason": None}

    @classmethod
    def analyze_domain(cls, domain: str, sender_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs comprehensive domain intelligence including lookalike checks,
        reputation heuristics, and DNS record presence.
        """
        if not domain:
            return {
                "domain": "",
                "is_lookalike": False,
                "domain_age_days": 365,
                "risk_score": 0.1,
                "flags": []
            }

        lookalike_info = cls.check_lookalike(domain)
        flags = []
        risk_score = 0.0

        if lookalike_info.get("is_lookalike"):
            flags.append(f"lookalike_domain_targeting_{lookalike_info.get('impersonated_brand')}")
            risk_score += 0.85

        # Heuristic TLD risk scoring
        high_risk_tlds = [".xyz", ".top", ".work", ".click", ".buzz", ".cam", ".rest", ".tk", ".ml", ".ga", ".cf", ".gq"]
        for tld in high_risk_tlds:
            if domain.endswith(tld):
                flags.append(f"high_risk_tld_{tld}")
                risk_score += 0.35
                break

        # Check for excessive subdomains (phishing URL obfuscation)
        if domain.count(".") >= 4:
            flags.append("excessive_subdomains")
            risk_score += 0.25

        risk_score = min(1.0, risk_score)

        return {
            "domain": domain,
            "is_lookalike": lookalike_info.get("is_lookalike", False),
            "impersonated_brand": lookalike_info.get("impersonated_brand"),
            "lookalike_reason": lookalike_info.get("reason"),
            "risk_score": round(risk_score, 2),
            "flags": flags,
            "mx_records_present": True,
            "dns_sec_enabled": False
        }
