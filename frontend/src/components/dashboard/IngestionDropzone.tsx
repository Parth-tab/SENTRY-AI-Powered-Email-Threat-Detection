import React, { useState } from "react";
import { UploadCloud, FileText, ArrowRight, Loader2, Sparkles, CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";
import { uploadEmlFile, submitRawEmail } from "../../services/api";

interface IngestionDropzoneProps {
  onEmailIngested: (emailDetail: any) => void;
}

export const IngestionDropzone: React.FC<IngestionDropzoneProps> = ({ onEmailIngested }) => {
  const [activeMode, setActiveMode] = useState<"file" | "raw">("file");
  const [rawContent, setRawContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [batchSummary, setBatchSummary] = useState<any | null>(null);

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
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsLoading(true);
    setErrorMsg(null);
    setBatchSummary(null);

    try {
      if (files.length === 1) {
        const res = await uploadEmlFile(files[0]);
        if (res.summary || res.source_format === "archive" || res.source_format === "csv") {
          setBatchSummary(res);
        } else {
          onEmailIngested(res);
        }
      } else {
        // Multi-file upload
        const formData = new FormData();
        Array.from(files).forEach((f) => formData.append("files", f));
        const response = await fetch("/api/v1/emails/batch/upload", {
          method: "POST",
          body: formData
        });
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || "Failed to process batch upload");
        }
        const batchRes = await response.json();
        setBatchSummary(batchRes);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload and analyze email");
    } finally {
      setIsLoading(false);
      // Reset input value so same files can be re-selected
      e.target.value = "";
    }
  };

  const handleRawSubmit = async () => {
    if (!rawContent.trim()) return;

    setIsLoading(true);
    setErrorMsg(null);
    setBatchSummary(null);

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
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-mono">
              RFC 5322 • ZIP • CSV
            </span>
          </h2>
          <p className="text-xs text-zinc-400">
            Submit emails via RFC 5322 single/batch upload, ZIP archive, CSV ground-truth dataset, or raw stream
          </p>
        </div>
        <div className="flex bg-[#121215] p-1 rounded-lg border border-[#27272A] space-x-1">
          <button
            onClick={() => setActiveMode("file")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              activeMode === "file" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Batch / File Upload
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
        <div
          className="border-2 border-dashed border-[#3F3F46] hover:border-rose-500/50 rounded-lg p-6 text-center transition-colors bg-[#121215]/50 flex flex-col items-center justify-center"
          aria-describedby="dropzone-helper-text"
        >
          <UploadCloud className="w-9 h-9 text-zinc-400 mb-2" />
          <p className="text-xs text-zinc-300 font-medium">Drag and drop email files (.eml, .msg, .mbox, .csv, .zip, extensionless)</p>
          <p className="text-[11px] text-zinc-500 mt-1 mb-3">
            Multi-hop parser, in-memory ZIP corpus streaming, and CSV ground-truth synthesizer
          </p>
          <p id="dropzone-helper-text" className="sr-only">
            Upload RFC 5322 EML, MSG, MBOX, ZIP, or CSV files for automated forensic triage and hash chain sealing
          </p>
          <label className="cursor-pointer px-4 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 active:bg-rose-700 text-white text-xs font-semibold shadow-md shadow-rose-500/20 transition-all flex items-center space-x-2">
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>Browse Local Files</span>
            <input
              type="file"
              accept=".eml,.msg,.mbox,.csv,.tsv,.zip,.txt,*"
              multiple
              onChange={handleFileUpload}
              disabled={isLoading}
              aria-describedby="dropzone-helper-text"
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

      {/* Batch Summary Notification Card */}
      {batchSummary && (
        <div className="mt-4 p-4 rounded-lg bg-[#121215] border border-emerald-500/30 text-xs text-zinc-200 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[11px]">
                Batch Ingestion Complete ({batchSummary.source_format || "batch"})
              </span>
            </div>
            <button
              onClick={() => setBatchSummary(null)}
              className="text-zinc-500 hover:text-zinc-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-4 gap-2 pt-2 border-t border-zinc-800/60 text-center font-mono">
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <div className="text-[10px] text-zinc-400">Total Entries</div>
              <div className="text-sm font-bold text-zinc-100">{batchSummary.summary?.total_entries ?? 0}</div>
            </div>
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <div className="text-[10px] text-emerald-400">Ingested (New)</div>
              <div className="text-sm font-bold text-emerald-400">{batchSummary.summary?.ingested ?? 0}</div>
            </div>
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <div className="text-[10px] text-amber-400">Duplicates</div>
              <div className="text-sm font-bold text-amber-400">{batchSummary.summary?.duplicates ?? 0}</div>
            </div>
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <div className="text-[10px] text-zinc-400">Elapsed</div>
              <div className="text-sm font-bold text-zinc-300">{batchSummary.summary?.elapsed_seconds ?? 0}s</div>
            </div>
          </div>

          {batchSummary.source_format === "csv" && (
            <div className="flex items-center space-x-2 p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]">
              <Info className="w-3.5 h-3.5 shrink-0" />
              <span>
                <strong>D4 Degradation Applied:</strong> Content and linguistic NLP analysis active. Transport headers, relay hops, and authentication records are marked unavailable (headerless source).
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
