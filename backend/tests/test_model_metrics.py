import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.content_analysis import ContentAnalysisService
from app.services.domain_intel import DomainIntelService
from app.services.geo_origin import GeoOriginService
from app.ml.classifier import ThreatClassifier

@pytest.mark.asyncio
async def test_model_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/model/metrics")
        assert response.status_code == 200
        data = response.json()

        # Metadata validation
        assert data["model_metadata"]["model_name"] == "SENTRY-GBDT-ATTN-Ensemble"
        assert data["model_metadata"]["feature_dimensions"] == 47
        assert data["model_metadata"]["validation_dataset_size"] >= 10000

        # Aggregate performance validation
        metrics = data["aggregate_metrics"]
        assert metrics["overall_accuracy"] >= 0.90
        assert metrics["macro_f1"] >= 0.90
        assert metrics["roc_auc_score"] >= 0.95

        # Confusion matrix validation
        cm = data["confusion_matrix"]
        assert len(cm["labels"]) == 5
        assert len(cm["matrix"]) == 5
        assert len(cm["matrix"][0]) == 5

        # Feature importances validation
        features = data["feature_importances"]
        assert len(features) >= 8
        assert features[0]["importance"] > 0.10

        # Calibration curve validation
        calibration = data["calibration_curve"]
        assert len(calibration) == 10

@pytest.mark.asyncio
async def test_model_features_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/model/features")
        assert response.status_code == 200
        data = response.json()
        assert data["total_features"] == 47
        assert "feature_importances" in data

def test_adversarial_zero_width_space_evasion_detection():
    # Evasion with zero-width spaces in "URGENT" and "wire transfer"
    raw_eml = b"""From: ceo@corporation-payroll.com
To: victim@company.com
Subject: U\xe2\x80\x8bR\xe2\x80\x8bG\xe2\x80\x8bE\xe2\x80\x8bN\xe2\x80\x8bT: Account Action
Content-Type: text/plain; charset="UTF-8"

Please process the w\xe2\x80\x8bi\xe2\x80\x8br\xe2\x80\x8be transfer immediately to the bank account.
"""
    parsed = IngestionService.parse_raw_email(raw_eml, source="adversarial_test")
    content_res = ContentAnalysisService.analyze_content(parsed)
    
    assert content_res["urgency_score"] > 0.0
    assert content_res["financial_score"] > 0.0

def test_adversarial_punycode_idn_evasion_detection():
    domain = "xn--gogle-qqa.com"
    domain_res = DomainIntelService.check_lookalike(domain)
    assert domain_res["is_lookalike"] is True
