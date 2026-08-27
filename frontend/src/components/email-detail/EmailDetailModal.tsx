import React, { useState } from "react";
import {
  X,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  FileDown,
  Globe,
  Network,
  Lock,
  Layers,
  Fingerprint,
  Copy,
  Check,
  Code,
  Eye,
  Terminal
} from "lucide-react";
import { FullEmailDetail, ThreatLevel } from "../../types";
import { getPdfReportUrl } from "../../services/api";

interface EmailDetailModalProps {
  emailDetail: FullEmailDetail | null;
  onClose: () => void;
  onOpenReportView?: (emailId: string) => void;
}

export const EmailDetailModal: React.FC<EmailDetailModalProps> = ({
  emailDetail,
  onClose,
  onOpenReportView
}) => {
  if (!emailDetail) return null;

  const { email, analysis, evidence } = emailDetail;
  const [activeTab, setActiveTab] = useState<"clean" | "raw_body" | "headers">("clean");
  const [copiedIoc, setCopiedIoc] = useState<string | null>(null);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIoc(id);
    setTimeout(() => setCopiedIoc(null), 2000);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return "#FA7273"; // Rose / Red
    if (score >= 0.70) return "#F59E0B"; // Amber
    if (score >= 0.40) return "#EAB308"; // Yellow
    return "#10B981"; // Emerald Green
  };

  const threatColor = getScoreColor(analysis.overall_threat_score);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#121215] border border-[#27272A] rounded-2xl w-full max-w-7xl h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Top Header */}
        <div className="h-14 border-b border-[#27272A] px-6 flex items-center justify-between bg-[#18181B]">
          <div className="flex items-center space-x-3">
            <span
              className="px-2.5 py-0.5 rounded text-xs font-mono font-bold uppercase border"
              style={{
                backgroundColor: `${threatColor}20`,
                color: threatColor,
                borderColor: `${threatColor}50`
              }}
            >
              {analysis.threat_level} THREAT ({analysis.overall_threat_score.toFixed(2)})
            </span>
            <span className="text-xs text-zinc-400 font-mono">
              CASE: {evidence?.chain_of_custody_id || "COC-PENDING"}
            </span>
            <span className="text-zinc-600">|</span>
            <span className="text-xs text-zinc-300 font-medium truncate max-w-md">
              {email.subject}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <a
              href={getPdfReportUrl(email.id)}
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-rose-500/20 transition-colors"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Export Forensic PDF</span>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Split-Screen Main Body */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
          {/* Left Column (5 Cols): Sanitized Email Reader */}
          <div className="lg:col-span-5 border-r border-[#27272A] flex flex-col bg-[#0E0E11] overflow-hidden">
            {/* Sender Metadata Box */}
            <div className="p-4 border-b border-[#27272A] bg-[#141418] space-y-2">
              <div>
                <span className="text-[10px] font-mono uppercase text-zinc-500">Subject</span>
                <div className="text-sm font-semibold text-zinc-100">{email.subject}</div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[10px] font-mono uppercase text-zinc-500">From</span>
                  <div className="text-zinc-300 font-mono truncate">{email.sender}</div>
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase text-zinc-500">To</span>
                  <div className="text-zinc-300 font-mono truncate">{email.recipient || "Undisclosed"}</div>
                </div>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 pt-1">
                <span>SHA-256: {email.sha256_hash.substring(0, 16)}...</span>
                <span>Hops: {analysis.relay_hops_count}</span>
              </div>
            </div>

            {/* Email View Selector */}
            <div className="px-4 py-2 border-b border-[#27272A] flex items-center justify-between bg-[#121215]">
              <div className="flex space-x-1">
                <button
                  onClick={() => setActiveTab("clean")}
                  className={`px-2.5 py-1 rounded text-xs font-medium flex items-center space-x-1 ${
                    activeTab === "clean" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Eye className="w-3 h-3" />
                  <span>Sanitized Body</span>
                </button>
                <button
                  onClick={() => setActiveTab("headers")}
                  className={`px-2.5 py-1 rounded text-xs font-medium flex items-center space-x-1 ${
                    activeTab === "headers" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Terminal className="w-3 h-3" />
                  <span>RFC Headers</span>
                </button>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                XSS Sanitized
              </span>
            </div>

            {/* Email Content Body */}
            <div className="flex-1 p-5 overflow-y-auto font-sans text-xs text-zinc-200 leading-relaxed">
              {activeTab === "clean" ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-[#18181B] border border-[#27272A] whitespace-pre-wrap font-sans">
                    {email.raw_content || "(Empty message body)"}
                  </div>
                </div>
              ) : (
                <pre className="text-[11px] font-mono text-zinc-300 bg-[#09090B] p-4 rounded-lg border border-[#27272A] overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(email.raw_headers, null, 2)}
                </pre>
              )}
            </div>
          </div>

          {/* Right Column (7 Cols): Forensic Intelligence & Attribution */}
          <div className="lg:col-span-7 flex flex-col bg-[#121215] overflow-y-auto p-6 space-y-6">
            {/* Top Row: Threat Radial Gauge & Multi-Class Confidence */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Radial Meter Card */}
              <div className="p-4 rounded-xl bg-[#18181B] border border-[#27272A] flex flex-col items-center justify-center text-center">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-zinc-800"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      strokeDasharray={`${analysis.overall_threat_score * 100}, 100`}
                      strokeWidth="3.5"
                      stroke={threatColor}
                      strokeLinecap="round"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <span className="text-xl font-bold font-mono text-white">
                      {(analysis.overall_threat_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-[9px] uppercase font-mono text-zinc-400">Risk Score</span>
                  </div>
                </div>
                <span className="mt-2 text-xs font-semibold text-zinc-200">
                  {analysis.primary_classification.toUpperCase()}
                </span>
                <span className="text-[10px] text-zinc-500 font-mono">
                  Confidence: {(analysis.classification_confidence * 100).toFixed(0)}%
                </span>
              </div>

              {/* Model Contributions Breakdown */}
              <div className="p-4 rounded-xl bg-[#18181B] border border-[#27272A] md:col-span-2 flex flex-col justify-between">
                <div className="text-xs font-semibold text-zinc-200 flex items-center justify-between">
                  <span>Classification Ensemble Triangulation</span>
                  <span className="text-[10px] font-mono text-zinc-500">3-Layer Pipeline</span>
                </div>
                <div className="space-y-2 my-2">
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-zinc-400 mb-1">
                      <span>Rule Engine (Deterministic IOCs)</span>
                      <span className="text-zinc-200">{((analysis.model_contributions?.rule_engine ?? 0) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-rose-500 rounded-full"
                        style={{ width: `${(analysis.model_contributions?.rule_engine ?? 0) * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-zinc-400 mb-1">
                      <span>Gradient Boosting (47 Engineered Features)</span>
                      <span className="text-zinc-200">{((analysis.model_contributions?.xgboost ?? 0) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full"
                        style={{ width: `${(analysis.model_contributions?.xgboost ?? 0) * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-zinc-400 mb-1">
                      <span>Linguistic Attention (Urgency & Impersonation)</span>
                      <span className="text-zinc-200">{((analysis.model_contributions?.transformer ?? 0) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded-full"
                        style={{ width: `${(analysis.model_contributions?.transformer ?? 0) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
                <div className="text-[10px] text-zinc-500">
                  Target Metrics: &gt;95% Precision, &gt;90% Recall
                </div>
              </div>
            </div>

            {/* Authentication Matrix Card */}
            <div className="p-4 rounded-xl bg-[#18181B] border border-[#27272A] space-y-3">
              <div className="text-xs font-semibold text-zinc-200 flex items-center space-x-2">
                <Lock className="w-3.5 h-3.5 text-zinc-400" />
                <span>RFC Authentication Verification (SPF / DKIM / DMARC)</span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {/* SPF */}
                <div className="p-3 rounded-lg bg-[#121215] border border-[#27272A]">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-zinc-300">SPF (RFC 7208)</span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                        analysis.auth_spf?.result === "pass"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                          : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                      }`}
                    >
                      {analysis.auth_spf?.result || "NONE"}
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-400 mt-1 leading-snug">
                    {analysis.auth_spf?.detail}
                  </p>
                </div>

                {/* DKIM */}
                <div className="p-3 rounded-lg bg-[#121215] border border-[#27272A]">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-zinc-300">DKIM (RFC 6376)</span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                        analysis.auth_dkim?.result === "pass"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                      }`}
                    >
                      {analysis.auth_dkim?.result || "NONE"}
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-400 mt-1 leading-snug">
                    {analysis.auth_dkim?.detail}
                  </p>
                </div>

                {/* DMARC */}
                <div className="p-3 rounded-lg bg-[#121215] border border-[#27272A]">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-zinc-300">DMARC (RFC 7489)</span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                        analysis.auth_dmarc?.result === "pass"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                          : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                      }`}
                    >
                      {analysis.auth_dmarc?.result || "NONE"}
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-400 mt-1 leading-snug">
                    {analysis.auth_dmarc?.detail}
                  </p>
                </div>
              </div>
            </div>

            {/* Origin Geolocation & Anonymity Card */}
            <div className="p-4 rounded-xl bg-[#18181B] border border-[#27272A] space-y-3">
              <div className="text-xs font-semibold text-zinc-200 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Globe className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Origin Geolocation & Anonymization Assessment</span>
                </div>
                <span className="text-[11px] font-mono text-zinc-400">
                  Confidence: {((analysis.origin_assessment?.confidence ?? 0) * 100).toFixed(0)}%
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-[#121215] border border-[#27272A] space-y-1.5">
                  <div className="text-[10px] font-mono uppercase text-zinc-500">Earliest Reliable Hop</div>
                  <div className="font-mono font-bold text-zinc-100 text-sm">
                    {analysis.origin_assessment?.probable_origin_ip}
                  </div>
                  <div className="text-zinc-400 text-xs">
                    {analysis.origin_assessment?.geolocation?.city},{" "}
                    {analysis.origin_assessment?.geolocation?.country} (
                    {analysis.origin_assessment?.geolocation?.country_code})
                  </div>
                  <div className="text-zinc-500 text-[11px]">
                    ASN: {analysis.origin_assessment?.geolocation?.asn} (
                    {analysis.origin_assessment?.geolocation?.isp})
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#121215] border border-[#27272A] space-y-2">
                  <div className="text-[10px] font-mono uppercase text-zinc-500">Anonymization Vectors</div>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.origin_assessment?.anonymization?.tor_exit_node && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
                        TOR EXIT NODE
                      </span>
                    )}
                    {analysis.origin_assessment?.anonymization?.vpn_detected && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-400 border border-purple-500/40">
                        VPN ({analysis.origin_assessment?.anonymization?.vpn_provider})
                      </span>
                    )}
                    {analysis.origin_assessment?.anonymization?.hosting_provider && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40">
                        CLOUD / VPS HOSTING
                      </span>
                    )}
                    {!analysis.origin_assessment?.anonymization?.tor_exit_node &&
                      !analysis.origin_assessment?.anonymization?.vpn_detected &&
                      !analysis.origin_assessment?.anonymization?.hosting_provider && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                          DIRECT RESIDENTIAL / ENTERPRISE ISP
                        </span>
                      )}
                  </div>
                  <p className="text-[10px] text-zinc-400 leading-snug">
                    {analysis.origin_assessment?.anonymization?.risk_summary}
                  </p>
                </div>
              </div>
            </div>

            {/* Campaign Attribution & Correlation */}
            <div className="p-4 rounded-xl bg-[#18181B] border border-[#27272A] space-y-2">
              <div className="text-xs font-semibold text-zinc-200 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Network className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Graph Campaign Attribution</span>
                </div>
                {analysis.attribution_assessment?.campaign_id && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/40">
                    {analysis.attribution_assessment.campaign_id}
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-300">
                {analysis.attribution_assessment?.assessment}
              </p>
              {analysis.attribution_assessment?.infrastructure_cluster && (
                <div className="p-2.5 rounded bg-[#121215] border border-[#27272A] text-[11px] font-mono text-zinc-400 flex items-center justify-between">
                  <span>Cluster: {analysis.attribution_assessment.infrastructure_cluster.name}</span>
                  <span className="text-rose-400 font-bold">
                    {analysis.attribution_assessment.related_emails} Correlated Incidents
                  </span>
                </div>
              )}
            </div>

            {/* Extracted IOCs */}
            <div className="p-4 rounded-xl bg-[#18181B] border border-[#27272A] space-y-2">
              <div className="text-xs font-semibold text-zinc-200">
                Extracted Indicators of Compromise (IOCs)
              </div>
              <div className="space-y-1.5">
                {analysis.content_analysis?.urls_found?.map((u, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded bg-[#121215] border border-[#27272A] text-xs font-mono"
                  >
                    <div className="truncate max-w-md text-zinc-300">
                      <span className="text-rose-400">[URL]</span> {u.url}
                    </div>
                    <button
                      onClick={() => copyToClipboard(u.url, `url-${i}`)}
                      className="p-1 text-zinc-400 hover:text-white"
                    >
                      {copiedIoc === `url-${i}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                ))}
                {analysis.origin_assessment?.probable_origin_ip && (
                  <div className="flex items-center justify-between p-2 rounded bg-[#121215] border border-[#27272A] text-xs font-mono">
                    <div className="text-zinc-300">
                      <span className="text-amber-400">[IP]</span> {analysis.origin_assessment.probable_origin_ip}
                    </div>
                    <button
                      onClick={() => copyToClipboard(analysis.origin_assessment.probable_origin_ip, "ip-origin")}
                      className="p-1 text-zinc-400 hover:text-white"
                    >
                      {copiedIoc === "ip-origin" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Actionable Recommendations */}
            <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-700 space-y-2">
              <div className="text-xs font-semibold text-zinc-100">
                Incident Response Countermeasures
              </div>
              <ul className="space-y-1 text-xs text-zinc-300">
                {analysis.recommendations?.map((r, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-rose-400 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
