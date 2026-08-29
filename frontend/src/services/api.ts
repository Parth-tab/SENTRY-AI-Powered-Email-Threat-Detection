import {
  DashboardStats,
  EmailRecordItem,
  FullEmailDetail,
  CampaignItem,
  GraphData
} from "../types";

function getApiBase(): string {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== "undefined" && window.location.hostname) {
    const proto = window.location.protocol === "https:" ? "https:" : "http:";
    return `${proto}//${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

const API_BASE = getApiBase();

export async function fetchStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/api/v1/dashboard/stats`);
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  return res.json();
}

export async function fetchEmails(threatLevel?: string, sender?: string): Promise<EmailRecordItem[]> {
  const params = new URLSearchParams();
  if (threatLevel && threatLevel !== "ALL") params.append("threat_level", threatLevel);
  if (sender) params.append("sender", sender);
  
  const res = await fetch(`${API_BASE}/api/v1/emails?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch emails");
  return res.json();
}

export async function fetchEmailDetails(emailId: string): Promise<FullEmailDetail> {
  const res = await fetch(`${API_BASE}/api/v1/emails/${emailId}`);
  if (!res.ok) throw new Error("Failed to fetch email details");
  return res.json();
}

export async function uploadEmlFile(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  
  const res = await fetch(`${API_BASE}/api/v1/emails/upload`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload email");
  }
  return res.json();
}

export async function submitRawEmail(rawText: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/emails/raw`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: rawText
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to analyze raw email");
  }
  return res.json();
}

export async function fetchCampaigns(): Promise<CampaignItem[]> {
  const res = await fetch(`${API_BASE}/api/v1/campaigns`);
  if (!res.ok) throw new Error("Failed to fetch campaigns");
  return res.json();
}

export async function fetchGlobalGraph(): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/api/v1/campaigns/graph/all`);
  if (!res.ok) throw new Error("Failed to fetch network graph");
  return res.json();
}

export async function verifyHashChain(emailId: string): Promise<{
  email_id: string;
  chain_of_custody_id: string;
  is_valid: boolean;
  verification_message: string;
  total_steps_verified: number;
  root_genesis_hash: string;
  sealed_head_hash: string;
}> {
  const res = await fetch(`${API_BASE}/api/v1/evidence/verify/${emailId}`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Failed to verify evidence hash chain");
  return res.json();
}

export async function seedSampleScenarios(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/samples/seed`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Failed to seed sample threat scenarios");
  return res.json();
}

export function getPdfReportUrl(emailId: string): string {
  return `${API_BASE}/api/v1/emails/${emailId}/report/pdf`;
}
