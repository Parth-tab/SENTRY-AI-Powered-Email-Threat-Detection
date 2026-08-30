import networkx as nx
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict, Counter

class CorrelationEngine:
    # In-memory graph structure for ultra-fast local traversal and fallback
    _graph = nx.MultiDiGraph()
    _campaigns = {
        "CMP-2024-0034": {
            "id": "CMP-2024-0034",
            "name": "Operation GhostRelay (Credential Harvester)",
            "description": "Coordinated credential harvesting campaign targeting Apex National Bank customers via bulletproof AS205100 and lookalike domains.",
            "threat_level": "CRITICAL",
            "actor_sophistication": "medium-high",
            "infrastructure_cluster": {
                "name": "AS205100-GhostRelay-Cluster",
                "provider": "Jonas Bunde / F3 Netze (Tor Exit & Bulletproof VPS)",
                "first_seen": "2024-01-10T08:00:00Z",
                "email_count": 14
            },
            "asns": ["AS205100", "AS51852"],
            "domains": ["apex-secureverify.com", "onlineapex-kyc-update.com", "apex-netbanking-alert.xyz"],
            "first_seen": "2024-01-10T08:00:00Z",
            "last_seen": "2024-01-15T10:23:45Z",
            "total_emails": 14
        },
        "CMP-2024-0012": {
            "id": "CMP-2024-0012",
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
        },
        "CMP-2024-0089": {
            "id": "CMP-2024-0089",
            "name": "FinPhish Global Cloud Harvester",
            "description": "Cross-tenant OAuth token and Microsoft 365 / DocuSign credential phishing campaign with deceptive hyperlink redirection.",
            "threat_level": "CRITICAL",
            "actor_sophistication": "high",
            "infrastructure_cluster": {
                "name": "Cloudflare-Proxied-Bulletproof-Cluster",
                "provider": "Cloudflare Reverse Proxy & Bulletproof NGINX Relays",
                "first_seen": "2024-01-08T11:15:00Z",
                "email_count": 11
            },
            "asns": ["AS13335", "AS15169"],
            "domains": ["docusign-secure-review.com", "office365-security-portal.net", "workspace-auth-verify.com"],
            "first_seen": "2024-01-08T11:15:00Z",
            "last_seen": "2024-01-15T09:40:00Z",
            "total_emails": 11
        }
    }

    COLOR_MAP = {
        "Campaign": "#EC4899",           # Pink
        "CampaignSupernode": "#EC4899",  # Pink Supernode
        "Email": "#FA7273",              # Threat Red / Coral
        "Domain": "#38BDF8",             # Cyan
        "IPAddress": "#F59E0B",          # Amber
        "Person": "#A855F7",             # Purple
        "Infrastructure": "#10B981",     # Emerald
        "BrandTarget": "#6366F1"         # Indigo
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
        threat_score = analysis_data.get("overall_threat_score", 0.0)
        threat_level = analysis_data.get("threat_level", "LOW")
        g.add_node(
            email_id,
            id=email_id,
            type="Email",
            label=f"Email: {email_data.get('subject', '')[:25]}...",
            threat_score=threat_score,
            threat_level=threat_level
        )

        # 2. Sender Person Node (identify synthetic provenance placeholders)
        sender = email_data.get("sender", "")
        if sender:
            person_id = f"person:{sender}"
            is_synthetic = any(k in sender.lower() for k in ("csv-import", "bulk-import", "unknown.local", "synthetic"))
            g.add_node(
                person_id,
                id=person_id,
                type="Person",
                label=sender,
                display_name=email_data.get("from_raw", ""),
                is_synthetic=is_synthetic
            )
            g.add_edge(email_id, person_id, relationship="CLAIMS_SENDER")

        # 3. Domain Node
        sender_domain = email_data.get("sender_domain", "")
        if sender_domain:
            domain_id = f"domain:{sender_domain}"
            is_synthetic = "unknown.local" in sender_domain.lower()
            g.add_node(
                domain_id,
                id=domain_id,
                type="Domain",
                label=sender_domain,
                is_lookalike=analysis_data.get("domain_intel", {}).get("is_lookalike", False),
                is_synthetic=is_synthetic
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
            camp_info = cls._campaigns.get(camp_id, {})
            g.add_node(
                campaign_node_id,
                id=campaign_node_id,
                type="Campaign",
                label=f"Campaign: {camp_id}",
                name=camp_info.get("name", attrib.get("assessment", "Correlated Campaign")),
                threat_level=camp_info.get("threat_level", "HIGH")
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

        # 1. Check against GhostRelay Campaign (CMP-2024-0034)
        if (asn in ["AS205100", "AS51852"] or is_tor or sender_domain in cls._campaigns["CMP-2024-0034"]["domains"] or impersonated_brand in ["Apex National Bank", "Apex Commercial Bank"]):
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
                "assessment": "Organized credential harvesting campaign targeting Apex National Bank customers via Tor/bulletproof infrastructure."
            }

        # 2. Check against Executive BEC Syndicate (CMP-2024-0012)
        if (content_data.get("financial_score", 0.0) > 0.35 and content_data.get("authority_score", 0.0) > 0.3):
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

        # 3. Check against FinPhish Global Cloud Harvester (CMP-2024-0089)
        if (content_data.get("has_mismatched_links") or content_data.get("credential_score", 0.0) > 0.35 or impersonated_brand in ["Microsoft 365", "Google Workspace", "DocuSign", "PayPal"]):
            camp = cls._campaigns["CMP-2024-0089"]
            return {
                "campaign_id": "CMP-2024-0089",
                "campaign_confidence": 0.85,
                "related_emails": 11,
                "infrastructure_cluster": {
                    "name": camp["infrastructure_cluster"]["name"],
                    "provider": camp["infrastructure_cluster"]["provider"],
                    "first_seen": camp["first_seen"],
                    "email_count": 11
                },
                "actor_sophistication": "high",
                "assessment": "Global SaaS OAuth credential and document lure phishing syndicate."
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
    def get_available_campaigns(cls) -> List[Dict[str, Any]]:
        """Summarizes all campaigns currently present in the correlation engine for UI selectors."""
        g = cls._graph
        campaigns = []
        
        for camp_id, static_info in cls._campaigns.items():
            cnode = f"campaign:{camp_id}"
            if g.has_node(cnode):
                c_emails = [u for u, v, d in g.edges(data=True) if v == cnode and d.get("relationship") == "PART_OF"]
                email_count = len(c_emails)
            else:
                email_count = static_info.get("total_emails", 0)
                
            campaigns.append({
                "id": camp_id,
                "name": static_info.get("name", camp_id),
                "threat_level": static_info.get("threat_level", "HIGH"),
                "actor_sophistication": static_info.get("actor_sophistication", "medium"),
                "email_count": email_count,
                "description": static_info.get("description", "")
            })
            
        # Sort by threat severity then email count descending
        severity_order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
        campaigns.sort(key=lambda c: (severity_order.get(c["threat_level"], 0), c["email_count"]), reverse=True)
        return campaigns

    @classmethod
    def get_graph_data(
        cls,
        campaign_id: Optional[str] = None,
        mode: str = "cluster",
        max_nodes: int = 300,
        collapse_synthetic: bool = True
    ) -> Dict[str, Any]:
        """
        Exports the graph formatted for React / D3 / Canvas simulation with:
        - Mode 'cluster': Single campaign focus view (default to primary campaign if not specified)
        - Mode 'supernode': Aggregated campaign supernodes + shared infrastructure/brand hubs
        - Mode 'detailed': Full entity graph with stratified diversity capping
        """
        if len(cls._graph.nodes) == 0:
            cls._populate_seed_cluster()

        available_campaigns = cls.get_available_campaigns()
        
        # Determine primary default campaign if not provided
        primary_campaign_id = available_campaigns[0]["id"] if available_campaigns else "CMP-2024-0034"
        active_campaign_id = campaign_id if (campaign_id and campaign_id != "all") else primary_campaign_id

        if mode == "supernode":
            res = cls._build_supernode_graph(collapse_synthetic=collapse_synthetic)
            res["mode"] = "supernode"
            res["active_campaign_id"] = "all"
            res["available_campaigns"] = available_campaigns
            return res

        elif mode == "detailed":
            res = cls._build_diversity_capped_graph(max_nodes=max_nodes, collapse_synthetic=collapse_synthetic)
            res["mode"] = "detailed"
            res["active_campaign_id"] = campaign_id or "all"
            res["available_campaigns"] = available_campaigns
            return res

        else: # Default: mode == "cluster"
            res = cls._build_cluster_graph(active_campaign_id, max_nodes=max_nodes, collapse_synthetic=collapse_synthetic)
            res["mode"] = "cluster"
            res["active_campaign_id"] = active_campaign_id
            res["available_campaigns"] = available_campaigns
            return res

    @classmethod
    def _build_cluster_graph(cls, campaign_id: str, max_nodes: int = 300, collapse_synthetic: bool = True) -> Dict[str, Any]:
        """Extracts the contextual neighborhood for a single targeted campaign cluster."""
        g = cls._graph
        cnode = f"campaign:{campaign_id}"
        
        if not g.has_node(cnode):
            # Fallback if specific campaign node doesn't exist
            cnode = [n for n, d in g.nodes(data=True) if d.get("type") == "Campaign"]
            cnode = cnode[0] if cnode else None

        if not cnode:
            return {"nodes": [], "links": []}

        # 1. Identify all emails attached to this campaign
        c_emails = [u for u, v, d in g.edges(data=True) if v == cnode and d.get("relationship") == "PART_OF"]
        
        cluster_nodes: Set[str] = set([cnode] + c_emails)
        for em in c_emails:
            for _, neighbor in g.out_edges(em):
                cluster_nodes.add(neighbor)
            for neighbor, _ in g.in_edges(em):
                cluster_nodes.add(neighbor)
        for _, neighbor in g.out_edges(cnode):
            cluster_nodes.add(neighbor)

        # 2-hop extension: Expand domains to BrandTargets and IPs to Infrastructure ASNs
        extended = set(cluster_nodes)
        for n in cluster_nodes:
            for _, neighbor in g.out_edges(n):
                if g.nodes[neighbor].get("type") in ("BrandTarget", "Infrastructure", "Domain"):
                    extended.add(neighbor)
        cluster_nodes = extended

        # Handle synthetic filtering if requested
        if collapse_synthetic:
            synthetic_nodes = [n for n in cluster_nodes if g.nodes[n].get("is_synthetic")]
            # Keep synthetic nodes marked distinctly
            for n in synthetic_nodes:
                g.nodes[n]["is_synthetic"] = True

        subg = g.subgraph(cluster_nodes)
        
        # Apply diversity cap if cluster is larger than max_nodes
        if subg.number_of_nodes() > max_nodes:
            subg = cls._apply_cluster_diversity_cap(subg, cnode, max_nodes)

        nodes, links = cls._format_subgraph_payload(subg)
        return {"nodes": nodes, "links": links, "cluster_campaign_id": campaign_id}

    @classmethod
    def _build_supernode_graph(cls, collapse_synthetic: bool = True) -> Dict[str, Any]:
        """Collapses campaigns into CampaignSupernodes and aggregates shared infrastructure / brand hubs."""
        g = cls._graph
        super_nodes = []
        super_links = defaultdict(int)
        link_details = defaultdict(list)
        
        campaign_nodes = [n for n, d in g.nodes(data=True) if d.get("type") == "Campaign"]
        if not campaign_nodes:
            campaign_nodes = ["campaign:CMP-2024-0034"]

        for cnode in campaign_nodes:
            cdata = g.nodes.get(cnode, {})
            camp_id = cnode.replace("campaign:", "")
            c_emails = [u for u, v, d in g.edges(data=True) if v == cnode and d.get("relationship") == "PART_OF"]
            email_count = max(len(c_emails), 1)
            
            infra_set = set()
            brand_set = set()
            domain_set = set()
            ip_set = set()
            
            for em in c_emails:
                for _, neighbor, edata in g.out_edges(em, data=True):
                    ntype = g.nodes[neighbor].get("type")
                    if ntype == "IPAddress":
                        ip_set.add(neighbor)
                        for _, inf in g.out_edges(neighbor):
                            if g.nodes[inf].get("type") == "Infrastructure":
                                infra_set.add(inf)
                    elif ntype == "Person":
                        for _, dom in g.out_edges(neighbor):
                            if g.nodes[dom].get("type") == "Domain":
                                domain_set.add(dom)
                                for _, br in g.out_edges(dom):
                                    if g.nodes[br].get("type") == "BrandTarget":
                                        brand_set.add(br)
                                        
            # Also check direct campaign connections
            for _, neighbor, edata in g.out_edges(cnode, data=True):
                ntype = g.nodes[neighbor].get("type")
                if ntype == "Infrastructure":
                    infra_set.add(neighbor)
                elif ntype == "IPAddress":
                    ip_set.add(neighbor)
                    
            supernode_id = f"supernode:{camp_id}"
            camp_info = cls._campaigns.get(camp_id, {})
            super_nodes.append({
                "id": supernode_id,
                "type": "CampaignSupernode",
                "label": camp_info.get("name", cdata.get("name", camp_id)),
                "campaign_id": camp_id,
                "threat_level": camp_info.get("threat_level", cdata.get("threat_level", "CRITICAL")),
                "threat_score": 0.92 if camp_info.get("threat_level") == "CRITICAL" else 0.78,
                "color": cls.COLOR_MAP["CampaignSupernode"],
                "email_count": email_count,
                "domain_count": len(domain_set),
                "ip_count": len(ip_set),
                "infra_count": len(infra_set),
                "badge_count": email_count,
                "details": {
                    "campaign_id": camp_id,
                    "name": camp_info.get("name", cdata.get("name", camp_id)),
                    "threat_level": camp_info.get("threat_level", "CRITICAL"),
                    "actor_sophistication": camp_info.get("actor_sophistication", "high"),
                    "email_count": email_count,
                    "domain_count": len(domain_set),
                    "ip_count": len(ip_set),
                    "infra_count": len(infra_set)
                }
            })
            
            # Collapse multi-edges to Infrastructure ASNs
            for inf in infra_set:
                super_links[(supernode_id, inf, "USES_INFRASTRUCTURE")] += email_count
                link_details[(supernode_id, inf, "USES_INFRASTRUCTURE")].append(f"{email_count} emails routed via {inf}")
                
            # Collapse multi-edges to Brand Targets
            for br in brand_set:
                super_links[(supernode_id, br, "TARGETS_BRAND")] += max(len(domain_set), 1)
                link_details[(supernode_id, br, "TARGETS_BRAND")].append(f"Targeting {br}")

        # Assemble included hub nodes
        included_infra = set(tgt for src, tgt, rel in super_links.keys() if g.has_node(tgt) and g.nodes[tgt].get("type") == "Infrastructure")
        included_brands = set(tgt for src, tgt, rel in super_links.keys() if g.has_node(tgt) and g.nodes[tgt].get("type") == "BrandTarget")
        
        nodes = list(super_nodes)
        for inf in included_infra:
            idata = g.nodes[inf]
            usage_count = sum(cnt for (src, tgt, rel), cnt in super_links.items() if tgt == inf)
            nodes.append({
                "id": inf,
                "type": "Infrastructure",
                "label": idata.get("label", inf),
                "color": cls.COLOR_MAP["Infrastructure"],
                "badge_count": usage_count,
                "threat_score": 0.85,
                "threat_level": "HIGH",
                "details": {**idata, "usage_count": usage_count}
            })
            
        for br in included_brands:
            bdata = g.nodes[br]
            usage_count = sum(cnt for (src, tgt, rel), cnt in super_links.items() if tgt == br)
            nodes.append({
                "id": br,
                "type": "BrandTarget",
                "label": bdata.get("label", br),
                "color": cls.COLOR_MAP["BrandTarget"],
                "badge_count": usage_count,
                "threat_score": 0.90,
                "threat_level": "CRITICAL",
                "details": {**bdata, "target_pressure": usage_count}
            })

        links = []
        for (src, tgt, rel), weight in super_links.items():
            links.append({
                "source": src,
                "target": tgt,
                "relationship": rel,
                "weight": weight,
                "count": weight,
                "relationship_summary": "; ".join(link_details.get((src, tgt, rel), []))
            })

        return {"nodes": nodes, "links": links}

    @classmethod
    def _build_diversity_capped_graph(cls, max_nodes: int = 300, collapse_synthetic: bool = True) -> Dict[str, Any]:
        """Builds full graph using stratified diversity allocation across all campaigns (G-D8 / P0-B)."""
        g = cls._graph
        total_nodes = g.number_of_nodes()
        
        if total_nodes <= max_nodes:
            nodes, links = cls._format_subgraph_payload(g)
            return {"nodes": nodes, "links": links}

        # Stratified diversity quota allocation
        campaign_nodes = [n for n, d in g.nodes(data=True) if d.get("type") == "Campaign"]
        num_camps = max(len(campaign_nodes), 1)
        per_camp_budget = max(max_nodes // num_camps, 20)
        
        selected_nodes: Set[str] = set()
        
        for cnode in campaign_nodes:
            c_emails = [u for u, v, d in g.edges(data=True) if v == cnode and d.get("relationship") == "PART_OF"]
            selected_nodes.add(cnode)
            
            # Sort emails by threat score descending
            c_emails.sort(key=lambda e: g.nodes[e].get("threat_score", 0.0), reverse=True)
            top_emails = c_emails[: min(len(c_emails), per_camp_budget // 2)]
            selected_nodes.update(top_emails)
            
            # Gather domain, IP, brand, infra for these top emails
            for em in top_emails:
                for _, neighbor in g.out_edges(em):
                    ntype = g.nodes[neighbor].get("type")
                    if ntype in ("IPAddress", "Domain", "Person"):
                        selected_nodes.add(neighbor)
                        for _, sub in g.out_edges(neighbor):
                            if g.nodes[sub].get("type") in ("Infrastructure", "BrandTarget"):
                                selected_nodes.add(sub)
                                
        # Add high-degree shared bridge entities
        degree_sorted = sorted(g.degree, key=lambda d: d[1], reverse=True)
        for nid, deg in degree_sorted:
            if len(selected_nodes) >= max_nodes:
                break
            selected_nodes.add(nid)

        subg = g.subgraph(selected_nodes)
        nodes, links = cls._format_subgraph_payload(subg)
        return {"nodes": nodes, "links": links}

    @classmethod
    def _apply_cluster_diversity_cap(cls, subg: nx.MultiDiGraph, cnode: str, max_nodes: int) -> nx.MultiDiGraph:
        """Applies diversity allocation within a single oversized campaign cluster."""
        selected = set([cnode])
        
        # Partition by type
        by_type = defaultdict(list)
        for n, d in subg.nodes(data=True):
            if n != cnode:
                by_type[d.get("type", "Other")].append(n)
                
        # Priority: Infrastructure, BrandTargets, Domains, IPs, Emails
        for t in ["Infrastructure", "BrandTarget"]:
            selected.update(by_type.get(t, []))
            
        # Top domains by threat/degree
        domains = sorted(by_type.get("Domain", []), key=lambda d: subg.degree(d), reverse=True)
        selected.update(domains[:30])
        
        # Top IPs
        ips = sorted(by_type.get("IPAddress", []), key=lambda i: subg.degree(i), reverse=True)
        selected.update(ips[:40])
        
        # Top Emails by threat score
        emails = sorted(by_type.get("Email", []), key=lambda e: subg.nodes[e].get("threat_score", 0.0), reverse=True)
        remaining_slots = max(max_nodes - len(selected), 10)
        selected.update(emails[:remaining_slots])
        
        return subg.subgraph(selected)

    @classmethod
    def _format_subgraph_payload(cls, subg: nx.MultiDiGraph) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Converts a NetworkX subgraph into React/Canvas node and collapsed-link payloads."""
        nodes = []
        links_map = defaultdict(int)
        link_details = defaultdict(list)

        for node_id, data in subg.nodes(data=True):
            node_type = data.get("type", "Unknown")
            is_synthetic = data.get("is_synthetic", False)
            deg = subg.degree(node_id)
            nodes.append({
                "id": str(node_id),
                "label": data.get("label", str(node_id)),
                "type": node_type,
                "color": cls.COLOR_MAP.get(node_type, "#94A3B8"),
                "threat_score": data.get("threat_score", 0.0),
                "threat_level": data.get("threat_level", "LOW"),
                "badge_count": deg,
                "degree": deg,
                "is_synthetic": is_synthetic,
                "details": data
            })

        for u, v, data in subg.edges(data=True):
            rel = data.get("relationship", "RELATED_TO")
            links_map[(str(u), str(v), rel)] += 1

        links = [
            {
                "source": u,
                "target": v,
                "relationship": rel,
                "weight": count,
                "count": count
            }
            for (u, v, rel), count in links_map.items()
        ]

        return nodes, links

    @classmethod
    def reset_graph(cls):
        """Clears in-memory graph and re-initializes the seed cluster."""
        cls._graph.clear()
        cls._populate_seed_cluster()

    @classmethod
    def _populate_seed_cluster(cls):
        """Pre-seeds the correlation graph with campaign CMP-2024-0034 cluster nodes."""
        g = cls._graph
        camp_id = "campaign:CMP-2024-0034"
        g.add_node(camp_id, id=camp_id, type="Campaign", label="Campaign: CMP-2024-0034", name="Operation GhostRelay", threat_level="CRITICAL")
        
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
            ("domain:apex-secureverify.com", "apex-secureverify.com", "Apex National Bank"),
            ("domain:onlineapex-kyc-update.com", "onlineapex-kyc-update.com", "Apex National Bank"),
            ("domain:apex-netbanking-alert.xyz", "apex-netbanking-alert.xyz", "Apex Commercial Bank")
        ]
        for d_id, d_label, brand in domains:
            g.add_node(d_id, id=d_id, type="Domain", label=d_label, is_lookalike=True)
            brand_id = f"domain:legit_{brand.lower().replace(' ', '_')}"
            g.add_node(brand_id, id=brand_id, type="BrandTarget", label=brand)
            g.add_edge(d_id, brand_id, relationship="LOOKALIKE_OF")
            g.add_edge(camp_id, d_id, relationship="DISTRIBUTES_VIA")
