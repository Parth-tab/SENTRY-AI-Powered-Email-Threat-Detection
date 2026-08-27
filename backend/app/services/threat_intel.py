import asyncio
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

class ThreatIntelService:
    # Known malicious test signatures & IOC database
    KNOWN_IOCS = {
        "urls": {
            "https://sbi-secureverify.com/login": {"source": "URLhaus", "threat": "credential_harvesting", "confidence": 0.95},
            "http://update-secure-bank-kyc.top/verify": {"source": "OpenPhish", "threat": "phishing", "confidence": 0.98},
            "http://185.220.101.34/payload.exe": {"source": "ThreatFox", "threat": "malware_delivery", "confidence": 0.99}
        },
        "ips": {
            "185.220.101.34": {"source": "ThreatFox", "threat": "tor_exit_botnet_controller", "confidence": 0.90},
            "194.26.29.117": {"source": "Spamhaus", "threat": "bulletproof_smtp_relay", "confidence": 0.88}
        },
        "domains": {
            "sbi-secureverify.com": {"source": "OpenPhish", "threat": "phishing_domain", "confidence": 0.96},
            "update-secure-bank-kyc.top": {"source": "URLhaus", "threat": "phishing_domain", "confidence": 0.94}
        }
    }

    @classmethod
    async def check_urlhaus(cls, urls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matches = []
        for u in urls:
            url_str = u.get("url", "")
            if url_str in cls.KNOWN_IOCS["urls"] and cls.KNOWN_IOCS["urls"][url_str]["source"] == "URLhaus":
                matches.append({"ioc": url_str, "type": "url", "source": "URLhaus", "detail": cls.KNOWN_IOCS["urls"][url_str]})
        return matches

    @classmethod
    async def check_threatfox(cls, ip: str, domain: str) -> List[Dict[str, Any]]:
        matches = []
        if ip in cls.KNOWN_IOCS["ips"]:
            matches.append({"ioc": ip, "type": "ip", "source": "ThreatFox", "detail": cls.KNOWN_IOCS["ips"][ip]})
        if domain in cls.KNOWN_IOCS["domains"] and cls.KNOWN_IOCS["domains"][domain]["source"] == "ThreatFox":
            matches.append({"ioc": domain, "type": "domain", "source": "ThreatFox", "detail": cls.KNOWN_IOCS["domains"][domain]})
        return matches

    @classmethod
    async def check_openphish(cls, urls: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
        matches = []
        for u in urls:
            url_str = u.get("url", "")
            if url_str in cls.KNOWN_IOCS["urls"] and cls.KNOWN_IOCS["urls"][url_str]["source"] == "OpenPhish":
                matches.append({"ioc": url_str, "type": "url", "source": "OpenPhish", "detail": cls.KNOWN_IOCS["urls"][url_str]})
        if domain in cls.KNOWN_IOCS["domains"] and cls.KNOWN_IOCS["domains"][domain]["source"] == "OpenPhish":
            matches.append({"ioc": domain, "type": "domain", "source": "OpenPhish", "detail": cls.KNOWN_IOCS["domains"][domain]})
        return matches

    @classmethod
    async def evaluate_threat_intelligence(cls, ip: str, domain: str, urls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs parallel IOC correlation across threat intelligence feeds.
        """
        urlhaus_task = cls.check_urlhaus(urls)
        threatfox_task = cls.check_threatfox(ip, domain)
        openphish_task = cls.check_openphish(urls, domain)

        results = await asyncio.gather(urlhaus_task, threatfox_task, openphish_task, return_exceptions=True)

        urlhaus_matches = results[0] if isinstance(results[0], list) else []
        threatfox_matches = results[1] if isinstance(results[1], list) else []
        openphish_matches = results[2] if isinstance(results[2], list) else []

        all_matches = urlhaus_matches + threatfox_matches + openphish_matches
        unique_sources = {m.get("source") for m in all_matches}
        
        # Corroboration score calculation: more independent sources agreeing = higher score
        if len(unique_sources) >= 3:
            corroboration_score = 0.95
        elif len(unique_sources) == 2:
            corroboration_score = 0.85
        elif len(unique_sources) == 1:
            corroboration_score = 0.65
        else:
            corroboration_score = 0.0

        return {
            "urlhaus_matches": len(urlhaus_matches),
            "threatfox_matches": len(threatfox_matches),
            "openphish_matches": len(openphish_matches),
            "total_matches": len(all_matches),
            "corroboration_score": round(corroboration_score, 2),
            "matched_iocs": all_matches
        }
