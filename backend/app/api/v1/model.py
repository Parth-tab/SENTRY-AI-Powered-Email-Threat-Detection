from typing import Dict, Any, List
from fastapi import APIRouter
from app.services.ml_metrics import MLMetricsService
from app.ml.feature_extractor import MLFeatureExtractor

router = APIRouter(prefix="/model", tags=["ML Model"])

@router.get("/metrics", response_model=Dict[str, Any])
async def get_model_metrics():
    """
    Returns comprehensive model validation metrics, confusion matrix,
    ROC-AUC, calibration curve, and top feature importance rankings.
    """
    return MLMetricsService.get_model_evaluation_metrics()

@router.get("/features", response_model=Dict[str, Any])
async def get_model_feature_definitions():
    """
    Returns the complete 47-dimension feature vector taxonomy extracted by SENTRY.
    """
    metrics = MLMetricsService.get_model_evaluation_metrics()
    return {
        "total_features": 47,
        "feature_importances": metrics["feature_importances"],
        "model_architecture": metrics["model_metadata"]["architecture"]
    }
