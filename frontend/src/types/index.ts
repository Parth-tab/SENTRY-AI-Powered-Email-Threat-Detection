export type ThreatLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type ClassificationType = "phishing" | "bec" | "impersonation" | "suspicious" | "legitimate";

export interface EmailRecordItem {
  id: string;
  message_id?: string;
  subject: string;
  sender: string;
  sender_domain?: string;
  recipient?: string;
  date?: string;
  source: string;
  sha256_hash: string;
  ingested_at: string;
  status: string;
  threat_score: number;
  threat_level: ThreatLevel;
  primary_classification: ClassificationType;
  origin_ip: string;
  origin_country: string;
}

export interface GeolocationInfo {
  ip: string;
  country: string;
  country_code: string;
  city: string;
  latitude: number;
  longitude: number;
  isp: string;
  asn: string;
  connection_type: string;
}

export interface AnonymizationFlags {
  tor_exit_node: boolean;
  vpn_detected: boolean;
  vpn_provider?: string;
  hosting_provider: boolean;
  hosting_details?: any;
  open_relay: boolean;
  risk_summary: string;
}

export interface OriginAssessment {
  probable_origin_ip: string;
  geolocation: GeolocationInfo;
  anonymization: AnonymizationFlags;
  confidence: number;
  confidence_factors: string[];
}

export interface RelayHop {
  hop_number: number;
  raw: string;
  from_host?: string;
  from_ip?: string;
  by_host?: string;
  protocol: string;
  timestamp?: string;
  is_private: boolean;
  is_reliable: boolean;
  hop_type: string;
}

export interface AnalysisDetail {
  id: string;
  email_id: string;
  overall_threat_score: number;
  threat_level: ThreatLevel;
  primary_classification: ClassificationType;
  classification_confidence: number;
  model_contributions: {
    rule_engine: number;
    xgboost: number;
    transformer: number;
  };
  auth_spf?: {
    result?: string;
    detail?: string;
    score?: number;
    status?: string;
    reason?: string;
  };
  auth_dkim?: {
    result?: string;
    detail?: string;
    score?: number;
    status?: string;
    reason?: string;
  };
  auth_dmarc?: {
    result?: string;
    policy?: string;
    alignment?: string;
    detail?: string;
    score?: number;
    status?: string;
    reason?: string;
  };
  header_anomalies: string[];
  relay_hops_count: number;
  relay_path: RelayHop[];
  earliest_reliable_hop?: RelayHop;
  content_analysis: {
    urgency_score: number;
    authority_score: number;
    financial_score: number;
    credential_score: number;
    structural_risk_score: number;
    action_requested: string;
    linguistic_features: {
      urgency_keywords: string[];
      authority_references: string[];
      financial_requests: string[];
      credential_harvesting: string[];
      generic_greetings: string[];
    };
    attention_tokens: string[];
    urls_found: Array<{
      url: string;
      domain: string;
      display_text: string;
      is_mismatch: boolean;
    }>;
    urls_count: number;
    has_mismatched_links: boolean;
    has_html_form: boolean;
    has_password_input: boolean;
    has_dangerous_attachment: boolean;
    attachment_names: string[];
  };
  domain_intel: {
    domain: string;
    is_lookalike: boolean;
    impersonated_brand?: string;
    lookalike_reason?: string;
    risk_score: number;
    flags: string[];
  };
  origin_assessment: OriginAssessment;
  attribution_assessment: {
    campaign_id?: string;
    campaign_confidence: number;
    related_emails: number;
    infrastructure_cluster?: {
      name: string;
      provider: string;
      first_seen: string;
      email_count: number;
    };
    actor_sophistication: string;
    assessment: string;
  };
  threat_intel_matches: {
    urlhaus_matches: number;
    threatfox_matches: number;
    openphish_matches: number;
    total_matches: number;
    corroboration_score: number;
    matched_iocs: Array<{
      ioc: string;
      type: string;
      source: string;
    }>;
  };
  recommendations: string[];
  created_at: string;
}

export interface ChainEntry {
  step_number: number;
  action: string;
  actor: string;
  timestamp: string;
  details: string;
  code_version: string;
  prev_hash: string;
  entry_hash: string;
}

export interface EvidenceDetail {
  id: string;
  email_id: string;
  sha256_hash: string;
  stored_path: string;
  chain_of_custody_id: string;
  chain_entries: ChainEntry[];
  last_entry_hash: string;
  is_sealed: boolean;
  created_at: string;
}

export interface FullEmailDetail {
  email: {
    id: string;
    message_id?: string;
    subject: string;
    sender: string;
    sender_domain?: string;
    recipient?: string;
    date?: string;
    source: string;
    sha256_hash: string;
    ingested_at: string;
    status: string;
    raw_content?: string;
    raw_headers?: Record<string, any>;
  };
  analysis: AnalysisDetail;
  evidence: EvidenceDetail;
}

export interface DashboardStats {
  total_emails_analyzed: number;
  threat_distribution: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  classification_breakdown: {
    phishing: number;
    bec: number;
    impersonation: number;
    suspicious: number;
    legitimate: number;
  };
  active_campaigns_count: number;
  avg_threat_score: number;
  top_origin_countries: Array<{
    country: string;
    code: string;
    count: number;
    threat_level: string;
  }>;
  recent_alerts: Array<{
    id: string;
    email_id: string;
    title: string;
    severity: ThreatLevel;
    message: string;
    threat_score: number;
    created_at: string;
  }>;
}

export interface CampaignItem {
  id: string;
  name: string;
  description: string;
  threat_level: ThreatLevel;
  actor_sophistication: string;
  infrastructure_cluster?: {
    name: string;
    provider: string;
    first_seen: string;
    email_count: number;
  };
  asns: string[];
  domains: string[];
  first_seen: string;
  last_seen: string;
  total_emails: number;
}

export interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    color: string;
    threat_score?: number;
    threat_level?: string;
    details?: any;
  }>;
  links: Array<{
    source: string;
    target: string;
    relationship: string;
  }>;
  total_entities_in_db?: number;
  queried_entities_count?: number;
}
