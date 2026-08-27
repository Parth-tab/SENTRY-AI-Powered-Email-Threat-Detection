import React, { useState } from "react";
import { ShieldAlert, AlertTriangle, CheckCircle2, Search, ArrowUpRight, Shield } from "lucide-react";
import { EmailRecordItem, ThreatLevel } from "../../types";

interface LiveThreatFeedProps {
  emails: EmailRecordItem[];
  onSelectEmail: (emailId: string) => void;
  selectedEmailId?: string;
}

export const LiveThreatFeed: React.FC<LiveThreatFeedProps> = ({
  emails,
  onSelectEmail,
  selectedEmailId
}) => {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredEmails = emails.filter((e) => {
    const matchesFilter = filterLevel === "ALL" || e.threat_level === filterLevel;
    const matchesSearch =
      searchTerm === "" ||
      e.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.sender.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.origin_ip.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getThreatBadge = (level: ThreatLevel, score: number) => {
    switch (level) {
      case "CRITICAL":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 flex items-center space-x-1">
            <ShieldAlert className="w-2.5 h-2.5" />
            <span>CRITICAL ({score.toFixed(2)})</span>
          </span>
        );
      case "HIGH":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40 flex items-center space-x-1">
            <AlertTriangle className="w-2.5 h-2.5" />
            <span>HIGH ({score.toFixed(2)})</span>
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/40">
            MEDIUM ({score.toFixed(2)})
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center space-x-1">
            <CheckCircle2 className="w-2.5 h-2.5" />
            <span>CLEAN ({score.toFixed(2)})</span>
          </span>
        );
    }
  };

  const getClassificationBadge = (cls: string) => {
    const colors: Record<string, string> = {
      phishing: "text-rose-400 bg-rose-500/10 border-rose-500/30",
      bec: "text-purple-400 bg-purple-500/10 border-purple-500/30",
      impersonation: "text-amber-400 bg-amber-500/10 border-amber-500/30",
      suspicious: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
      legitimate: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
    };
    return (
      <span
        className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono font-semibold border ${
          colors[cls] || "text-zinc-400 bg-zinc-800 border-zinc-700"
        }`}
      >
        {cls}
      </span>
    );
  };

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-xl shadow-sm overflow-hidden flex flex-col">
      {/* Header with Search and Filter */}
      <div className="p-4 border-b border-[#27272A] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#141418]">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100 flex items-center space-x-2">
            <span>Threat Intelligence Ingestion Stream</span>
            <span className="text-[11px] font-mono font-normal text-zinc-500">
              ({filteredEmails.length} artifacts)
            </span>
          </h2>
          <p className="text-xs text-zinc-400">
            Real-time multi-signal classified telemetry queue
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-zinc-500" />
            <input
              type="text"
              placeholder="Search sender, subject, IP..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-[#09090B] border border-[#27272A] rounded-lg pl-8 pr-3 py-1 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-rose-500/50 w-48"
            />
          </div>

          <div className="flex bg-[#09090B] p-0.5 rounded-lg border border-[#27272A]">
            {["ALL", "CRITICAL", "HIGH", "LOW"].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                className={`px-2.5 py-1 text-[10px] font-mono font-semibold rounded transition-colors ${
                  filterLevel === lvl
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-96">
        <table className="w-full text-left text-xs text-zinc-300">
          <thead className="bg-[#121215] text-[10px] font-mono uppercase text-zinc-400 border-b border-[#27272A] sticky top-0 z-10">
            <tr>
              <th className="py-2.5 px-4">Threat Level</th>
              <th className="py-2.5 px-4">Class</th>
              <th className="py-2.5 px-4">Subject & Sender</th>
              <th className="py-2.5 px-4">Origin IP / Country</th>
              <th className="py-2.5 px-4">Ingested At</th>
              <th className="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#27272A]/60">
            {filteredEmails.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-zinc-500">
                  No email artifacts matching criteria. Use the sandbox or click "Load Demo Scenarios".
                </td>
              </tr>
            ) : (
              filteredEmails.map((email) => {
                const isSelected = selectedEmailId === email.id;
                return (
                  <tr
                    key={email.id}
                    className={`hover:bg-zinc-800/40 transition-colors cursor-pointer ${
                      isSelected ? "bg-rose-500/10 border-l-2 border-rose-500" : ""
                    }`}
                    onClick={() => onSelectEmail(email.id)}
                  >
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getThreatBadge(email.threat_level, email.threat_score)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getClassificationBadge(email.primary_classification)}
                    </td>
                    <td className="py-3 px-4 max-w-xs">
                      <div className="font-medium text-zinc-200 truncate">{email.subject}</div>
                      <div className="text-[11px] text-zinc-400 truncate font-mono mt-0.5">
                        {email.sender}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap font-mono text-[11px]">
                      <div className="text-zinc-300">{email.origin_ip}</div>
                      <div className="text-zinc-500 text-[10px]">
                        {email.origin_country || "XX"}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-zinc-400 text-[11px] font-mono">
                      {new Date(email.ingested_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit"
                      })}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEmail(email.id);
                        }}
                        className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-rose-500/20 hover:text-rose-300 text-zinc-300 border border-zinc-700 text-[11px] font-medium transition-colors inline-flex items-center space-x-1"
                      >
                        <span>Investigate</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
