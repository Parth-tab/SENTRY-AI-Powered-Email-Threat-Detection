import {
  DashboardStats,
  EmailRecordItem,
  FullEmailDetail,
  CampaignItem,
  GraphData
} from "../types";

function getApiBase(): string {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  return "";
}

const API_BASE = getApiBase();

const AUTH_TOKEN_KEY = "sentry_auth_token";
const DEFAULT_DEMO_TOKEN = "sentry_operator_token_2025";

export function getAuthToken(): string {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(AUTH_TOKEN_KEY);
    if (stored) return stored;
    // Default demo token fallback for seamless operator experience
    return DEFAULT_DEMO_TOKEN;
  }
  return DEFAULT_DEMO_TOKEN;
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(AUTH_TOKEN_KEY, token.trim());
    window.dispatchEvent(new CustomEvent("sentry:auth_changed"));
  }
}

export function clearAuthToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    window.dispatchEvent(new CustomEvent("sentry:auth_changed"));
  }
}

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(res: Response, fallbackErrorMsg: string): Promise<any> {
  if (!res.ok) {
    if (res.status === 401) {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("sentry:unauthorized", { detail: { url: res.url } }));
      }
    }
    const err = await res.json().catch(() => ({}));
    const detailMsg = typeof err.detail === "object" ? err.detail.message : err.detail;
    throw new Error(detailMsg || fallbackErrorMsg);
  }
  return res.json();
}

export async function fetchStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/api/v1/dashboard/stats`);
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  return res.json();
}

export async function fetchEmails(threatLevel?: string, sender?: string, limit: number = 10000): Promise<EmailRecordItem[]> {
  const params = new URLSearchParams();
  if (threatLevel && threatLevel !== "ALL") params.append("threat_level", threatLevel);
  if (sender) params.append("sender", sender);
  params.append("limit", limit.toString());
  
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
    headers: getAuthHeaders(),
    body: formData
  });
  return handleResponse(res, "Failed to upload email");
}

export async function submitRawEmail(rawText: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/emails/raw`, {
    method: "POST",
    headers: getAuthHeaders({ "Content-Type": "text/plain" }),
    body: rawText
  });
  return handleResponse(res, "Failed to analyze raw email");
}

export async function fetchCampaigns(): Promise<CampaignItem[]> {
  const res = await fetch(`${API_BASE}/api/v1/campaigns`);
  if (!res.ok) throw new Error("Failed to fetch campaigns");
  return res.json();
}

export async function fetchGlobalGraph(params?: {
  campaignId?: string;
  mode?: "cluster" | "supernode" | "detailed";
  maxNodes?: number;
  collapseSynthetic?: boolean;
}): Promise<GraphData> {
  const query = new URLSearchParams();
  if (params?.campaignId) query.set("campaign_id", params.campaignId);
  if (params?.mode) query.set("mode", params.mode);
  if (params?.maxNodes) query.set("max_nodes", String(params.maxNodes));
  if (params?.collapseSynthetic !== undefined) query.set("collapse_synthetic", String(params.collapseSynthetic));

  const queryString = query.toString();
  const url = `${API_BASE}/api/v1/campaigns/graph/all${queryString ? `?${queryString}` : ""}`;
  const res = await fetch(url);
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
    method: "POST",
    headers: getAuthHeaders()
  });
  return handleResponse(res, "Failed to verify evidence hash chain");
}

export async function seedSampleScenarios(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/samples/seed`, {
    method: "POST",
    headers: getAuthHeaders()
  });
  return handleResponse(res, "Failed to seed sample threat scenarios");
}

export function getPdfReportUrl(emailId: string): string {
  return `${API_BASE}/api/v1/emails/${emailId}/report/pdf`;
}
