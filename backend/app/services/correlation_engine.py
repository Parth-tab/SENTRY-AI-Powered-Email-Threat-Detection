import networkx as nx
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class CorrelationEngine:
    # In-memory graph structure for ultra-fast local traversal and fallback
    _graph = nx.MultiDiGraph()
    _campaigns = {
        "CMP-2024-0034": {
            "name": "Operation GhostRelay (Credential Harvester)",
            "description": "Coordinated credential harvesting campaign targeting Indian banking customers via bulletproof AS205100 and lookalike domains.",
            "threat_level": "CRITICAL",
            "actor_sophistication": "medium-high",
            "infrastructure_cluster": {
                "name": "AS205100-GhostRelay-Cluster",
                "provider": "Jonas Bunde / F3 Netze (Tor Exit & Bulletproof VPS)",
                "first_seen": "2024-01-10T08:00:00Z",
                "email_count": 14
            },
            "asns": ["AS205100", "AS51852"],
            "domains": ["sbi-secureverify.com", "onlinesbi-kyc-update.com", "hdfc-netbanking-alert.xyz"],
            "first_seen": "2024-01-10T08:00:00Z",
            "last_seen": "2024-01-15T10:23:45Z",
            "total_emails": 14
        },
        "CMP-2024-0012": {
            "name": "CEO Wire Fraud BEC Syndicate",
            "description": "Executive display-name impersonation campaign requesting urgent payroll or vendor wire transfers to offshore accounts.",
            "threat_level": "HIGH",
            "actor_sophistication": "high",
            "infrastructure_cluster": {
                "name": "Scattered-Relay-Cluster",
                "provider": "Commercial VPN & Free Webmail Infrastructure",
                "first_seen": "2024-01-05T14:30:00Z",
                "email_count": 8
            },
            "asns": ["AS16509", "AS14061"],
            "domains": ["executive-corp-mail.com", "management-board-review.com"],
            "first_seen": "2024-01-05T14:30:00Z",
            "last_seen": "2024-01-14T18:12:00Z",
            "total_emails": 8
        }
    }

    @classmethod
    def get_campaign(cls, campaign_id: str) -> Optional[Dict[str, Any]]:
        return cls._campaigns.get(campaign_id)

    @classmethod
    def list_campaigns(cls) -> List[Dict[str, Any]]:
        return list(cls._campaigns.values())

    @classmethod
    def add_email_to_graph(cls, email_id: str, email_data: Dict[str, Any], analysis_data: Dict[str, Any]):
        """
        Adds nodes and edges for Email, Domain, IP, Person, and Campaign into the correlation graph.
        """
        g = cls._graph
        
        # 1. Email Node
        g.add_node(
            email_id,
            id=email_id,
            type="Email",
            label=f"Email: {email_data.get('subject', '')[:25]}...",
            threat_score=analysis_data.get("overall_threat_score", 0.0),
            threat_level=analysis_data.get("threat_level", "LOW")
        )

        # 2. Sender Person Node
        sender = email_data.get("sender", "")
        if sender:
            person_id = f"person:{sender}"
            g.add_node(person_id, id=person_id, type="Person", label=sender, display_name=email_data.get("from_raw", ""))
            g.add_edge(email_id, person_id, relationship="CLAIMS_SENDER")

        # 3. Domain Node
        sender_domain = email_data.get("sender_domain", "")
        if sender_domain:
            domain_id = f"domain:{sender_domain}"
            g.add_node(
                domain_id,
                id=domain_id,
                type="Domain",
                label=sender_domain,
                is_lookalike=analysis_data.get("domain_intel", {}).get("is_lookalike", False)
            )
            if sender:
                g.add_edge(f"person:{sender}", domain_id, relationship="HAS_ADDRESS")

            # Lookalike relationship if detected
            impersonated = analysis_data.get("domain_intel", {}).get("impersonated_brand")
            if impersonated:
                legit_id = f"domain:legit_{impersonated.lower().replace(' ', '_')}"
                g.add_node(legit_id, id=legit_id, type="BrandTarget", label=impersonated)
                g.add_edge(domain_id, legit_id, relationship="LOOKALIKE_OF")

        # 4. IP Address Node & Infrastructure
        origin = analysis_data.get("origin_assessment", {})
        ip = origin.get("probable_origin_ip")
        if ip and ip != "Unknown":
            ip_id = f"ip:{ip}"
            geo = origin.get("geolocation", {})
            g.add_node(
                ip_id,
                id=ip_id,
                type="IPAddress",
                label=f"{ip} ({geo.get('country_code', 'XX')})",
                asn=geo.get("asn"),
                isp=geo.get("isp"),
                is_tor=origin.get("anonymization", {}).get("tor_exit_node", False)
            )
            g.add_edge(email_id, ip_id, relationship="SENT_FROM")

            asn = geo.get("asn")
            if asn:
                infra_id = f"infra:{asn}"
                g.add_node(infra_id, id=infra_id, type="Infrastructure", label=f"{asn} ({geo.get('isp', '')})")
                g.add_edge(ip_id, infra_id, relationship="HOSTED_BY")

        # 5. Campaign Correlation
        attrib = analysis_data.get("attribution_assessment", {})
        camp_id = attrib.get("campaign_id")
        if camp_id:
            campaign_node_id = f"campaign:{camp_id}"
            g.add_node(
                campaign_node_id,
                id=campaign_node_id,
                type="Campaign",
                label=f"Campaign: {camp_id}",
                name=attrib.get("assessment", "Correlated Campaign")
            )
            g.add_edge(email_id, campaign_node_id, relationship="PART_OF")
            if ip and ip != "Unknown":
                g.add_edge(campaign_node_id, f"ip:{ip}", relationship="USES_INFRASTRUCTURE")

    @classmethod
    def correlate(cls, email_data: Dict[str, Any], origin_data: Dict[str, Any], domain_data: Dict[str, Any], content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes multi-entity graph correlation against known campaign clusters.
        """
        sender_domain = email_data.get("sender_domain", "")
        origin_ip = origin_data.get("probable_origin_ip", "")
        asn = origin_data.get("geolocation", {}).get("asn", "")
        is_tor = origin_data.get("anonymization", {}).get("tor_exit_node", False)
        impersonated_brand = domain_data.get("impersonated_brand")

        # Check against GhostRelay Campaign (CMP-2024-0034)
        if (asn == "AS205100" or is_tor or sender_domain in cls._campaigns["CMP-2024-0034"]["domains"] or impersonated_brand == "State Bank of India"):
            camp = cls._campaigns["CMP-2024-0034"]
            return {
                "campaign_id": "CMP-2024-0034",
                "campaign_confidence": 0.88,
                "related_emails": 14,
                "infrastructure_cluster": {
                    "name": camp["infrastructure_cluster"]["name"],
                    "provider": camp["infrastructure_cluster"]["provider"],
                    "first_seen": camp["first_seen"],
                    "email_count": 14
                },
                "actor_sophistication": "medium-high",
                "assessment": "Organized credential harvesting campaign targeting Indian banking customers via Tor/bulletproof infrastructure."
            }

        # Check against Executive BEC Syndicate (CMP-2024-0012)
        if (content_data.get("financial_score", 0.0) > 0.4 and content_data.get("authority_score", 0.0) > 0.3):
            camp = cls._campaigns["CMP-2024-0012"]
            return {
                "campaign_id": "CMP-2024-0012",
                "campaign_confidence": 0.82,
                "related_emails": 8,
                "infrastructure_cluster": {
                    "name": camp["infrastructure_cluster"]["name"],
                    "provider": camp["infrastructure_cluster"]["provider"],
                    "first_seen": camp["first_seen"],
                    "email_count": 8
                },
                "actor_sophistication": "high",
                "assessment": "Targeted Business Email Compromise (BEC) wire transfer fraud syndicate impersonating executive leadership."
            }

        return {
            "campaign_id": None,
            "campaign_confidence": 0.0,
            "related_emails": 1,
            "infrastructure_cluster": None,
            "actor_sophistication": "low",
            "assessment": "Isolated incident; no statistically significant campaign cluster detected."
        }

    @classmethod
    def get_graph_data(cls, focus_email_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Exports the graph formatted for React / D3 / react-force-graph.
        """
        nodes = []
        links = []
        
        # Color mapping for node types in UI
        color_map = {
            "Email": "#FA7273", # Threat Red / Coral
            "Domain": "#38BDF8", # Cyan
            "IPAddress": "#F59E0B", # Amber
            "Person": "#A855F7", # Purple
            "Campaign": "#EC4899", # Pink
            "Infrastructure": "#10B981", # Emerald
            "BrandTarget": "#6366F1" # Indigo
        }

        # If graph is empty, populate with default seed campaign cluster
        if len(cls._graph.nodes) == 0:
            cls._populate_seed_cluster()

        for node_id, data in cls._graph.nodes(data=True):
            node_type = data.get("type", "Unknown")
            nodes.append({
                "id": str(node_id),
                "label": data.get("label", str(node_id)),
                "type": node_type,
                "color": color_map.get(node_type, "#94A3B8"),
                "threat_score": data.get("threat_score", 0.0),
                "threat_level": data.get("threat_level", "LOW"),
                "details": data
            })

        for u, v, data in cls._graph.edges(data=True):
            links.append({
                "source": str(u),
                "target": str(v),
                "relationship": data.get("relationship", "RELATED_TO")
            })

        return {"nodes": nodes, "links": links}

    @classmethod
    def _populate_seed_cluster(cls):
        """Pre-seeds the correlation graph with campaign CMP-2024-0034 cluster nodes."""
        g = cls._graph
        camp_id = "campaign:CMP-2024-0034"
        g.add_node(camp_id, id=camp_id, type="Campaign", label="Campaign: CMP-2024-0034", name="Operation GhostRelay")
        
        infra_id = "infra:AS205100"
        g.add_node(infra_id, id=infra_id, type="Infrastructure", label="AS205100 (Jonas Bunde / F3 Netze)")
        g.add_edge(camp_id, infra_id, relationship="USES_INFRASTRUCTURE")

        # 3 correlated IPs
        ips = [
            ("ip:185.220.101.34", "185.220.101.34 (NL)", True),
            ("ip:185.220.101.5", "185.220.101.5 (NL)", True),
            ("ip:194.26.29.117", "194.26.29.117 (RU)", False)
        ]
        for i_id, label, is_tor in ips:
            g.add_node(i_id, id=i_id, type="IPAddress", label=label, is_tor=is_tor)
            g.add_edge(i_id, infra_id, relationship="HOSTED_BY")
            g.add_edge(camp_id, i_id, relationship="USES_INFRASTRUCTURE")

        # Lookalike domains
        domains = [
            ("domain:sbi-secureverify.com", "sbi-secureverify.com", "State Bank of India"),
            ("domain:onlinesbi-kyc-update.com", "onlinesbi-kyc-update.com", "State Bank of India"),
            ("domain:hdfc-netbanking-alert.xyz", "hdfc-netbanking-alert.xyz", "HDFC Bank")
        ]
        for d_id, d_label, brand in domains:
            g.add_node(d_id, id=d_id, type="Domain", label=d_label, is_lookalike=True)
            brand_id = f"domain:legit_{brand.lower().replace(' ', '_')}"
            g.add_node(brand_id, id=brand_id, type="BrandTarget", label=brand)
            g.add_edge(d_id, brand_id, relationship="LOOKALIKE_OF")
            g.add_edge(camp_id, d_id, relationship="DISTRIBUTES_VIA")
