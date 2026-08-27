import json
from datetime import datetime, date
import numpy as np

def json_serializable(obj):
    """
    Recursively converts datetime objects, numpy types, and sets into standard JSON serializable types.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_serializable(i) for i in obj]
    return obj
