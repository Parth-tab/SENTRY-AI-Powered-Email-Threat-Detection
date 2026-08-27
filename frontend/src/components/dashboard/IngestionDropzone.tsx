import React, { useState } from "react";
import { UploadCloud, FileText, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { uploadEmlFile, submitRawEmail } from "../../services/api";

interface IngestionDropzoneProps {
  onEmailIngested: (emailDetail: any) => void;
}

export const IngestionDropzone: React.FC<IngestionDropzoneProps> = ({ onEmailIngested }) => {
  const [activeMode, setActiveMode] = useState<"file" | "raw">("file");
  const [rawContent, setRawContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const samplePresets = [
    {
      name: "SBI KYC Phishing (Tor Origin)",
      content: `From: "State Bank of India Security" <support@sbi-secureverify.com>
To: target@victim.com
Subject: URGENT: Mandatory KYC Verification Required Within 24 Hours or Account Suspended
Date: Mon, 15 Jan 2024 10:23:40 +0000
Received: from mail.bulletproof-relay.net ([185.220.101.34]) by mx.victim.com with ESMTP; Mon, 15 Jan 2024 10:23:45 +0000

Dear Valued Customer, We detected unauthorized access to your account. You must verify your credentials within 24 hours at https://sbi-secureverify.com/login to prevent suspension.`
    },
    {
      name: "Executive BEC Wire Fraud",
      content: `From: "Alex Mercer - Chief Executive Officer" <ceo.alexmercer@gmail.com>
Reply-To: alex.mercer@executive-corp-mail.com
To: cfo@techcorp.com
Subject: Confidential: Immediate Out-of-Band Wire Transfer Request
Date: Tue, 16 Jan 2024 14:12:00 +0000
Received: from [194.26.29.117] by mx.techcorp.com with HTTP; Tue, 16 Jan 2024 14:12:00 +0000

Please initiate an urgent wire transfer of $142,500 to the overseas escrow account detailed below for Project Titan acquisition.`
    },
    {
      name: "Legitimate Google Workspace",
      content: `From: Google Workspace Team <engineering-updates@google.com>
To: engineer@company.com
Subject: Monthly Engineering Architecture & Security Summary
Date: Thu, 15 Jan 2024 10:23:55 -0800
Received: from mail-sor-f41.google.com ([209.85.220.41]) by mx.company.com with SMTPS; Thu, 15 Jan 2024 10:23:59 -0800
Authentication-Results: mx.company.com; dkim=pass; spf=pass; dmarc=pass

Hi Engineering Team, Here is your monthly summary of architecture updates and quarterly roadmap targets.`
    }
  ];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await uploadEmlFile(file);
      onEmailIngested(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload and analyze email");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRawSubmit = async () => {
    if (!rawContent.trim()) return;

    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await submitRawEmail(rawContent);
      onEmailIngested(res);
      setRawContent("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze raw email content");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-[#27272A] mb-4">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100 flex items-center space-x-2">
            <span>Forensic Ingestion Sandbox</span>
          </h2>
          <p className="text-xs text-zinc-400">
            Submit emails via RFC 5322 multipart upload or direct stream for instant triage
          </p>
        </div>
        <div className="flex bg-[#121215] p-1 rounded-lg border border-[#27272A] space-x-1">
          <button
            onClick={() => setActiveMode("file")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              activeMode === "file" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            File Upload (.eml)
          </button>
          <button
            onClick={() => setActiveMode("raw")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              activeMode === "raw" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Raw RFC 5322
          </button>
        </div>
      </div>

      {activeMode === "file" ? (
        <div className="border-2 border-dashed border-[#3F3F46] hover:border-rose-500/50 rounded-lg p-6 text-center transition-colors bg-[#121215]/50 flex flex-col items-center justify-center">
          <UploadCloud className="w-9 h-9 text-zinc-400 mb-2" />
          <p className="text-xs text-zinc-300 font-medium">Drag and drop email files (.eml, .msg, .mbox)</p>
          <p className="text-[11px] text-zinc-500 mt-1 mb-3">Multi-hop Received-header parser & RFC 3227 vault storage</p>
          <label className="cursor-pointer px-4 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 active:bg-rose-700 text-white text-xs font-semibold shadow-md shadow-rose-500/20 transition-all flex items-center space-x-2">
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>Browse Local Files</span>
            <input
              type="file"
              accept=".eml,.msg,.mbox,.txt"
              onChange={handleFileUpload}
              disabled={isLoading}
              className="hidden"
            />
          </label>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono text-zinc-400">Load sample:</span>
            {samplePresets.map((p, idx) => (
              <button
                key={idx}
                onClick={() => setRawContent(p.content)}
                className="text-[10px] px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 transition-colors"
              >
                {p.name}
              </button>
            ))}
          </div>

          <textarea
            value={rawContent}
            onChange={(e) => setRawContent(e.target.value)}
            placeholder="Paste raw email headers and body here (From:, To:, Subject:, Received:)..."
            rows={5}
            className="w-full bg-[#121215] border border-[#27272A] rounded-lg p-3 text-xs font-mono text-zinc-200 focus:outline-none focus:border-rose-500/60"
          />

          <div className="flex justify-end">
            <button
              onClick={handleRawSubmit}
              disabled={isLoading || !rawContent.trim()}
              className="px-4 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 disabled:opacity-50 text-white text-xs font-semibold flex items-center space-x-2 shadow-md shadow-rose-500/20"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ArrowRight className="w-3.5 h-3.5" />
              )}
              <span>Execute Forensic Triage</span>
            </button>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="mt-3 p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
          {errorMsg}
        </div>
      )}
    </div>
  );
};
