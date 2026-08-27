import React, { useState } from "react";
import {
  FileCheck2,
  ShieldCheck,
  ShieldAlert,
  FileDown,
  Lock,
  CheckCircle,
  AlertOctagon,
  Loader2,
  Key,
  Clock,
  Layers
} from "lucide-react";
import { FullEmailDetail, EmailRecordItem } from "../../types";
import { verifyHashChain, getPdfReportUrl } from "../../services/api";

interface ForensicReportViewProps {
  emails: EmailRecordItem[];
  selectedEmailDetail: FullEmailDetail | null;
  onSelectEmail: (id: string) => void;
}

export const ForensicReportView: React.FC<ForensicReportViewProps> = ({
  emails,
  selectedEmailDetail,
  onSelectEmail
}) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any | null>(null);

  const currentEmail = selectedEmailDetail;

  const handleVerify = async (emailId: string) => {
    setIsVerifying(true);
    try {
      const res = await verifyHashChain(emailId);
      setVerifyResult(res);
    } catch (err: any) {
      setVerifyResult({
        is_valid: false,
        verification_message: err.message || "Failed to verify chain"
      });
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Evidentiary Header Card */}
      <div className="p-6 rounded-2xl bg-[#18181B] border border-[#27272A] shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#27272A]">
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>RFC 3227 Evidentiary Vault & Chain-of-Custody Verifier</span>
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Cryptographically sealed audit trails and court-admissible forensic intelligence packages
            </p>
          </div>
          {currentEmail && (
            <a
              href={getPdfReportUrl(currentEmail.email.id)}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-rose-500/20 transition-colors self-start sm:self-auto"
            >
              <FileDown className="w-4 h-4" />
              <span>Download PDF Forensic Report</span>
            </a>
          )}
        </div>

        {/* Current Email Selection Picker */}
        <div className="flex items-center space-x-2 text-xs">
          <span className="text-zinc-400 font-mono">Selected Artifact:</span>
          <select
            value={currentEmail?.email?.id || ""}
            onChange={(e) => onSelectEmail(e.target.value)}
            className="bg-[#121215] border border-[#27272A] rounded-lg px-3 py-1.5 text-zinc-200 text-xs font-mono focus:outline-none focus:border-rose-500/50"
          >
            {emails.map((e) => (
              <option key={e.id} value={e.id}>
                [{e.threat_level}] {e.subject.substring(0, 45)}... ({e.sender})
              </option>
            ))}
          </select>
        </div>

        {currentEmail ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-4">
            {/* Chain of Custody Audit Log (7 Cols) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="p-4 rounded-xl bg-[#121215] border border-[#27272A] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Lock className="w-3.5 h-3.5 text-emerald-400" />
                    <h3 className="text-xs font-bold text-zinc-200 uppercase font-mono">
                      Cryptographic Audit Steps (SHA-256 Hash Chain)
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500">
                    ID: {currentEmail.evidence?.chain_of_custody_id}
                  </span>
                </div>

                <div className="space-y-2.5">
                  {currentEmail.evidence?.chain_entries?.map((entry, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-[#18181B] border border-[#27272A] text-xs font-mono space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-zinc-300">
                        <div className="flex items-center space-x-2">
                          <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 text-[10px] font-bold">
                            STEP #{entry.step_number}
                          </span>
                          <span className="font-bold text-zinc-100">{entry.action}</span>
                        </div>
                        <span className="text-[10px] text-zinc-500">
                          {new Date(entry.timestamp).toISOString()}
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-400 font-sans">{entry.details}</p>
                      <div className="text-[10px] text-zinc-500 truncate pt-1 border-t border-[#27272A]/50">
                        <span className="text-zinc-600">Entry Hash:</span>{" "}
                        <span className="text-emerald-400/80">{entry.entry_hash}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Cryptographic Verification Engine (5 Cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="p-5 rounded-xl bg-[#121215] border border-[#27272A] space-y-4">
                <div className="flex items-center space-x-2">
                  <Key className="w-4 h-4 text-rose-400" />
                  <h3 className="text-xs font-bold text-zinc-200 uppercase font-mono">
                    RFC 3227 Hash-Chain Tamper Verification
                  </h3>
                </div>

                <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                  Execute mathematical verification across all sequential hash links to prove evidence
                  immutability and guarantee zero post-acquisition tampering.
                </p>

                <button
                  onClick={() => handleVerify(currentEmail.email.id)}
                  disabled={isVerifying}
                  className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/20 transition-all font-mono"
                >
                  {isVerifying ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ShieldCheck className="w-4 h-4" />
                  )}
                  <span>{isVerifying ? "Verifying Math Chain..." : "Verify Hash Chain Integrity"}</span>
                </button>

                {verifyResult && (
                  <div
                    className={`p-4 rounded-lg border text-xs font-mono space-y-2 ${
                      verifyResult.is_valid
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                        : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                    }`}
                  >
                    <div className="flex items-center space-x-2 font-bold text-sm">
                      {verifyResult.is_valid ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-emerald-400" />
                          <span>INTEGRITY VERIFIED (PASS)</span>
                        </>
                      ) : (
                        <>
                          <AlertOctagon className="w-4 h-4 text-rose-400" />
                          <span>TAMPERING DETECTED (FAIL)</span>
                        </>
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed">{verifyResult.verification_message}</p>
                    {verifyResult.is_valid && (
                      <div className="pt-2 border-t border-emerald-500/20 text-[10px] space-y-1">
                        <div>
                          <span className="text-emerald-500 font-bold">Steps Verified:</span>{" "}
                          {verifyResult.total_steps_verified}
                        </div>
                        <div className="truncate">
                          <span className="text-emerald-500 font-bold">Sealed Head Hash:</span>{" "}
                          {verifyResult.sealed_head_hash}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="p-3 rounded-lg bg-[#18181B] border border-[#27272A] text-[11px] text-zinc-500 space-y-1 font-mono">
                  <div className="text-zinc-400 font-semibold">Evidentiary Standards Met:</div>
                  <div>• RFC 3227 Guidelines for Evidence Collection</div>
                  <div>• NIST SP 800-86 Forensic Integration</div>
                  <div>• ISO/IEC 27037 Digital Evidence Handling</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-zinc-500 font-mono text-xs">
            No email record selected.
          </div>
        )}
      </div>
    </div>
  );
};
