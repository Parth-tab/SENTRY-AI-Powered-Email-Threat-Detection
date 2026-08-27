from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any

# 1. Pipeline Counters & Rates
EMAILS_INGESTED_TOTAL = Counter(
    "sentry_emails_ingested_total",
    "Total number of emails ingested and processed by SENTRY",
    ["source", "status"]
)

THREAT_CLASSIFICATIONS_TOTAL = Counter(
    "sentry_threat_classifications_total",
    "Total threat classifications categorized by level and type",
    ["threat_level", "classification"]
)

THREAT_INTEL_LOOKUPS_TOTAL = Counter(
    "sentry_threat_intel_lookups_total",
    "Total IOC lookups performed across threat intelligence feeds",
    ["provider", "result"]
)

# 2. Latency & Duration Histograms
PIPELINE_DURATION_SECONDS = Histogram(
    "sentry_pipeline_duration_seconds",
    "End-to-end processing latency for raw email analysis",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# 3. Live Gauges
ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
    "sentry_active_websocket_connections",
    "Number of active real-time SOC analyst WebSocket telemetry connections"
)

DATABASE_QUERY_DURATION_SECONDS = Histogram(
    "sentry_database_query_duration_seconds",
    "Database execution duration in seconds",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

def record_email_processed(source: str, threat_level: str, classification: str, duration_sec: float):
    """Records telemetry counters and duration for an analyzed email."""
    EMAILS_INGESTED_TOTAL.labels(source=source, status="success").inc()
    THREAT_CLASSIFICATIONS_TOTAL.labels(threat_level=threat_level, classification=classification).inc()
    PIPELINE_DURATION_SECONDS.observe(duration_sec)

def get_prometheus_metrics() -> bytes:
    """Renders all registered Prometheus metrics in text/plain format."""
    return generate_latest()
