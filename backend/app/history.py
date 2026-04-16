import base64

from .database import get_analysis, list_analyses


def get_recent_analyses(user_id, limit=10):
    records = list_analyses(user_id, limit=limit)
    return [format_analysis(record, include_image=False) for record in records]


def get_analysis_detail(analysis_id):
    record = get_analysis(analysis_id)
    if not record:
        return None
    return format_analysis(record, include_image=True)


def format_analysis(record, include_image):
    payload = {
        "id": record["id"],
        "filename": record["filename"],
        "content_type": record["content_type"],
        "label": record["label"],
        "probabilities": record["probabilities"],
        "classes": record["classes"],
        "confidence": record["confidence"],
        "confidence_gap": record["confidence_gap"],
        "created_at": record["created_at"],
    }
    if include_image and record["image_bytes"] is not None:
        payload["image_base64"] = base64.b64encode(record["image_bytes"]).decode("utf-8")
    return payload
