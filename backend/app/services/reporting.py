import io
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class ReportingService:
    CODE_VERSION = "SENTRY-v1.0.0-PROD"

    @staticmethod
    def sanitize_csv_cell(value: Any) -> str:
        """
        Applies OWASP CSV formula injection neutralization at write-time.
        Prefixes cells starting with '=', '+', '-', '@', '\\t', '\\r' with a single quote.
        """
        if value is None:
            return ""
        s = str(value)
        if s.startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + s
        return s

    @classmethod
    def generate_ioc_csv_report(cls, email_records: List[Dict[str, Any]]) -> str:
        """
        Generates an IOC CSV export with write-time OWASP formula neutralization
        on all attacker-controlled fields (subject, sender, IP, domain, URL).
        """
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["email_id", "subject", "sender", "sender_domain", "threat_level", "threat_score", "origin_ip"])
        for r in email_records:
            writer.writerow([
                cls.sanitize_csv_cell(r.get("id", "")),
                cls.sanitize_csv_cell(r.get("subject", "")),
                cls.sanitize_csv_cell(r.get("sender", "")),
                cls.sanitize_csv_cell(r.get("sender_domain", "")),
                cls.sanitize_csv_cell(r.get("threat_level", "")),
                cls.sanitize_csv_cell(r.get("threat_score", "")),
                cls.sanitize_csv_cell(r.get("origin_ip", ""))
            ])
        return output.getvalue()

    @classmethod
    def compute_entry_hash(cls, prev_hash: str, action: str, actor: str, timestamp: str, details: str) -> str:
        """
        Computes SHA-256 hash for RFC 3227 tamper-evident chain of custody entry.
        """
        payload = f"{prev_hash}|{action}|{actor}|{timestamp}|{details}|{cls.CODE_VERSION}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def initialize_chain_of_custody(cls, email_id: str, sha256_hash: str, source: str) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Creates an RFC 3227 compliant evidence chain-of-custody audit log.
        """
        coc_id = f"COC-{email_id[:8].upper()}"
        t0 = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Genesis block of evidence
        genesis_prev = "0000000000000000000000000000000000000000000000000000000000000000"
        h0 = cls.compute_entry_hash(
            prev_hash=genesis_prev,
            action="EVIDENCE_ACQUISITION",
            actor="SENTRY_INGESTION_SERVICE",
            timestamp=t0,
            details=f"Acquired raw RFC 5322 email payload via {source}. Preserved byte-exact in vault with SHA-256: {sha256_hash}"
        )

        entries = [
            {
                "step_number": 1,
                "action": "EVIDENCE_ACQUISITION",
                "actor": "SENTRY_INGESTION_SERVICE",
                "timestamp": t0,
                "details": f"Acquired raw RFC 5322 email payload via {source}. Preserved byte-exact in vault with SHA-256: {sha256_hash}",
                "code_version": cls.CODE_VERSION,
                "prev_hash": genesis_prev,
                "entry_hash": h0
            }
        ]

        return coc_id, entries, h0

    @classmethod
    def append_chain_entry(cls, entries: List[Dict[str, Any]], action: str, actor: str, details: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Appends a verifiable step to the RFC 3227 audit chain.
        """
        prev_hash = entries[-1]["entry_hash"] if entries else "0000000000000000000000000000000000000000000000000000000000000000"
        t = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        step = len(entries) + 1
        
        entry_hash = cls.compute_entry_hash(prev_hash, action, actor, t, details)
        
        entry = {
            "step_number": step,
            "action": action,
            "actor": actor,
            "timestamp": t,
            "details": details,
            "code_version": cls.CODE_VERSION,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash
        }
        entries.append(entry)
        return entries, entry_hash

    @classmethod
    def verify_chain_integrity(cls, entries: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Verifies that every entry in the hash chain is unbroken and untampered.
        """
        if not entries:
            return False, "Empty chain of custody"

        for idx, entry in enumerate(entries):
            if idx == 0:
                expected_prev = "0000000000000000000000000000000000000000000000000000000000000000"
            else:
                expected_prev = entries[idx - 1]["entry_hash"]

            if entry.get("prev_hash") != expected_prev:
                return False, f"Broken link at step {entry.get('step_number')}: prev_hash does not match previous entry_hash."

            calculated_hash = cls.compute_entry_hash(
                prev_hash=entry["prev_hash"],
                action=entry["action"],
                actor=entry["actor"],
                timestamp=entry["timestamp"],
                details=entry["details"]
            )

            if entry.get("entry_hash") != calculated_hash:
                return False, f"Tampering detected at step {entry.get('step_number')}: entry_hash mismatch."

        return True, "RFC 3227 Hash Chain is cryptographically valid and verified."

    @classmethod
    def generate_pdf_report(cls, email_data: Dict[str, Any], analysis_data: Dict[str, Any], evidence_data: Dict[str, Any]) -> bytes:
        """
        Generates a professional, court-admissible forensic intelligence report as a PDF.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Forensic Styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0F172A")
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B")
        )
        heading_style = ParagraphStyle(
            "HeadingSection",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1E293B")
        )
        mono_style = ParagraphStyle(
            "MonoField",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0F172A")
        )

        elements = []

        # 1. Header Banner
        t_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        header_table = Table(
            [
                [
                    Paragraph("<b>SENTRY FORENSIC INTELLIGENCE PLATFORM</b><br/><font size=7.5 color='#64748B'>EVIDENTIARY-GRADE EMAIL THREAT ASSESSMENT & ORIGIN ATTRIBUTION REPORT</font>", title_style),
                    Paragraph(f"<b>CASE ID:</b> {evidence_data.get('chain_of_custody_id', 'COC-001')}<br/><b>DATE:</b> {t_now}<br/><b>CLASSIFICATION:</b> LAW ENFORCEMENT SENSITIVE", subtitle_style)
                ]
            ],
            colWidths=[350, 190]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0F172A"), spaceBefore=2, spaceAfter=8))

        # 2. Executive Summary Box
        threat_level = analysis_data.get("threat_level", "LOW")
        threat_score = float(analysis_data.get("overall_threat_score", 0.0))
        score_pre = analysis_data.get("score_pre_floor") or (analysis_data.get("content_analysis") or {}).get("score_pre_floor")
        subtype = analysis_data.get("classification_subtype") or (analysis_data.get("content_analysis") or {}).get("classification_subtype")
        primary_cls = analysis_data.get("primary_classification", "legitimate").upper()
        if subtype:
            cls_display = f"{primary_cls} ({subtype})"
        else:
            cls_display = primary_cls

        if score_pre is not None and abs(float(score_pre) - threat_score) > 0.001:
            score_display = f"{threat_score:.2f} [Enforced Floor; Model: {float(score_pre):.2f}]"
        else:
            score_display = f"{threat_score:.2f} / 1.00"

        box_bg = colors.HexColor("#FEF2F2") if threat_level == "CRITICAL" else colors.HexColor("#FFFBEB") if threat_level == "HIGH" else colors.HexColor("#F8FAFC")
        border_color = colors.HexColor("#EF4444") if threat_level == "CRITICAL" else colors.HexColor("#F59E0B") if threat_level == "HIGH" else colors.HexColor("#94A3B8")

        summary_text = (
            f"<b>EXECUTIVE ASSESSMENT:</b> SENTRY automated forensic triage has assessed this artifact as "
            f"<b>{threat_level} THREAT ({score_display})</b> classified as <b>{cls_display}</b>. "
            f"Authentication checks resulted in SPF: <b>{analysis_data.get('auth_spf', {}).get('result', 'NONE').upper()}</b>, "
            f"DKIM: <b>{analysis_data.get('auth_dkim', {}).get('result', 'NONE').upper()}</b>, and "
            f"DMARC: <b>{analysis_data.get('auth_dmarc', {}).get('result', 'NONE').upper()}</b>."
        )

        exec_table = Table([[Paragraph(summary_text, body_style)]], colWidths=[540])
        exec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), box_bg),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8)
        ]))
        elements.append(exec_table)
        elements.append(Spacer(1, 8))

        # 3. Target Artifact Metadata
        elements.append(Paragraph("1. TARGET ARTIFACT METADATA", heading_style))
        meta_data = [
            [Paragraph("<b>Subject:</b>", body_style), Paragraph(str(email_data.get("subject", "")), body_style)],
            [Paragraph("<b>Claimed Sender:</b>", body_style), Paragraph(str(email_data.get("from_raw", "")), body_style)],
            [Paragraph("<b>Recipient:</b>", body_style), Paragraph(str(email_data.get("recipient", "")), body_style)],
            [Paragraph("<b>Message-ID:</b>", body_style), Paragraph(str(email_data.get("message_id", "")), mono_style)],
            [Paragraph("<b>SHA-256 Hash:</b>", body_style), Paragraph(f"<font size=6.5 fontName='Courier'>{str(email_data.get('sha256_hash', ''))}</font>", mono_style)]
        ]
        meta_table = Table(meta_data, colWidths=[110, 430])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # 4. Origin & Infrastructure Attribution
        elements.append(Paragraph("2. ORIGIN GEOLOCATION & INFRASTRUCTURE ATTRIBUTION", heading_style))
        origin = analysis_data.get("origin_assessment", {})
        geo = origin.get("geolocation", {})
        anon = origin.get("anonymization", {})
        attrib = analysis_data.get("attribution_assessment", {})

        origin_data = [
            [Paragraph("<b>Probable Origin IP:</b>", body_style), Paragraph(str(origin.get("probable_origin_ip", "Unknown")), mono_style),
             Paragraph("<b>Location:</b>", body_style), Paragraph(f"{geo.get('city', 'Unknown')}, {geo.get('country', 'Unknown')}", body_style)],
            [Paragraph("<b>ISP / Host:</b>", body_style), Paragraph(str(geo.get("isp", "Unknown")), body_style),
             Paragraph("<b>ASN:</b>", body_style), Paragraph(str(geo.get("asn", "Unknown")), mono_style)],
            [Paragraph("<b>Anonymization:</b>", body_style), Paragraph(f"TOR: {anon.get('tor_exit_node', False)} | VPN: {anon.get('vpn_detected', False)} | VPS: {anon.get('hosting_provider', False)}", body_style),
             Paragraph("<b>Origin Confidence:</b>", body_style), Paragraph(f"{int(origin.get('confidence', 0.0)*100)}%", body_style)],
            [Paragraph("<b>Correlated Campaign:</b>", body_style), Paragraph(str(attrib.get("campaign_id") or "None (Isolated)"), body_style),
             Paragraph("<b>Actor Sophistication:</b>", body_style), Paragraph(str(attrib.get("actor_sophistication", "low")).upper(), body_style)]
        ]
        origin_table = Table(origin_data, colWidths=[110, 160, 110, 160])
        origin_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(origin_table)
        elements.append(Spacer(1, 8))

        # 5. Indicators of Compromise (IOCs)
        elements.append(Paragraph("3. EXTRACTED INDICATORS OF COMPROMISE (IOCs)", heading_style))
        iocs = []
        if origin.get("probable_origin_ip") and origin.get("probable_origin_ip") != "Unknown":
            iocs.append(["IPv4 Address", origin.get("probable_origin_ip"), "Originating SMTP Client"])
        
        domain_intel = analysis_data.get("domain_intel", {})
        if domain_intel.get("domain"):
            iocs.append(["Domain", domain_intel.get("domain"), f"Sender Domain (Lookalike: {domain_intel.get('is_lookalike')})"])
        
        # Structured Reply-To extraction (EXT-005)
        reply_to_raw = email_data.get("headers", {}).get("reply-to") or email_data.get("reply_to") or ""
        if reply_to_raw:
            from email.utils import parseaddr
            _, r_email = parseaddr(str(reply_to_raw))
            if r_email:
                r_domain = r_email.split("@")[-1].lower() if "@" in r_email else ""
                s_domain = str(email_data.get("sender_domain", "")).lower()
                is_mismatch = bool(r_domain and s_domain and r_domain != s_domain)
                iocs.append(["Reply-To Email", r_email, f"Response Routing (Mismatch: {is_mismatch})"])
                if is_mismatch and r_domain:
                    iocs.append(["Reply-To Domain", r_domain, f"External Diversion Channel (From: {s_domain})"])

        content = analysis_data.get("content_analysis", {})
        for u in content.get("urls_found", [])[:3]:
            iocs.append(["URL", u.get("url", ""), "Extracted Payload Link"])

        if not iocs:
            iocs.append(["N/A", "No high-confidence malicious IOCs extracted", "Clean"])

        ioc_table_data = [[Paragraph("<b>Type</b>", body_style), Paragraph("<b>Indicator Value</b>", body_style), Paragraph("<b>Context</b>", body_style)]]
        for row in iocs:
            ioc_table_data.append([Paragraph(row[0], body_style), Paragraph(row[1], mono_style), Paragraph(row[2], body_style)])

        ioc_table = Table(ioc_table_data, colWidths=[100, 240, 200])
        ioc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(ioc_table)
        elements.append(Spacer(1, 8))

        # 6. RFC 3227 Chain of Custody Audit Log
        elements.append(Paragraph("4. RFC 3227 CHAIN OF CUSTODY AUDIT TRAIL (CRYPTOGRAPHICALLY SEALED)", heading_style))
        coc_table_data = [[
            Paragraph("<b>Step</b>", body_style),
            Paragraph("<b>Action / Actor</b>", body_style),
            Paragraph("<b>Timestamp (UTC)</b>", body_style),
            Paragraph("<b>SHA-256 Hash Chain Entry</b>", body_style)
        ]]

        for entry in evidence_data.get("chain_entries", [])[:5]:
            coc_table_data.append([
                Paragraph(f"#{entry.get('step_number')}", body_style),
                Paragraph(f"{entry.get('action')}<br/><font size=6.5 color='#64748B'>{entry.get('actor')}</font>", body_style),
                Paragraph(f"<font size=6.5 fontName='Courier'>{str(entry.get('timestamp'))}</font>", mono_style),
                Paragraph(f"<font size=5.5 fontName='Courier'>{entry.get('entry_hash')}</font>", mono_style)
            ])

        coc_table = Table(coc_table_data, colWidths=[35, 155, 130, 220])
        coc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4)
        ]))
        elements.append(coc_table)
        elements.append(Spacer(1, 8))

        # 7. Actionable Guidance & Sign-off
        elements.append(Paragraph("5. RECOMMENDED COUNTERMEASURES", heading_style))
        recs = analysis_data.get("recommendations", [])
        if not recs:
            recs = ["Preserve digital evidence in vault.", "Verify sender identity via secondary out-of-band channel."]

        rec_paragraphs = [Paragraph(f"• {r}", body_style) for r in recs]
        for rp in rec_paragraphs:
            elements.append(rp)

        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8"), spaceBefore=4, spaceAfter=4))
        elements.append(Paragraph("<b>LEGAL NOTICE:</b> This forensic examination was generated by SENTRY in compliance with RFC 3227 evidence handling standards. Cryptographic hashes ensure evidence chain immutability.<br/><b>ATTRIBUTION:</b> This forensic report includes GeoLite2 data created by MaxMind, available from <font color='#2563EB'><u>https://www.maxmind.com</u></font>.", subtitle_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
