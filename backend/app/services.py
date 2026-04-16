import base64
import io
import sys
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image

# Add project root to sys.path to allow importing from 'model' directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from model.utils.gradcam import GradCAM
from model.utils.lime_explain import generate_lime
from model.utils.model_loader import load_model
from model.utils.predict import classes, predict_image, transform

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MODEL_PATH = PROJECT_ROOT / "model" / "model" / "alzheimer_resnet18.pth"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = load_model(str(MODEL_PATH))
    return _model


def read_image(file_bytes: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return image


def prepare_model_display_image(image: Image.Image) -> Image.Image:
    # Match the image geometry used by the model so explanation overlays stay aligned.
    return image.resize((224, 224), Image.Resampling.BILINEAR)


def build_prediction_payload(image: Image.Image):
    model = get_model()
    label, probabilities = predict_image(model, image)

    predicted_idx = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_idx])
    sorted_probs = np.sort(probabilities)[::-1]
    confidence_gap = (
        float(sorted_probs[0] - sorted_probs[1])
        if len(sorted_probs) > 1
        else float(sorted_probs[0])
    )

    return {
        "label": label,
        "probabilities": [float(value) for value in probabilities],
        "classes": classes,
        "confidence": confidence,
        "confidence_gap": confidence_gap,
    }


def _figure_to_base64(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def build_gradcam_explanation(image: Image.Image, overlay_opacity: float) -> str:
    model = get_model()
    image_tensor = transform(image).unsqueeze(0)
    gradcam = GradCAM(model, model.layer4)
    heatmap = gradcam.generate(image_tensor)
    display_image = prepare_model_display_image(image)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(display_image)
    ax.imshow(heatmap, cmap="jet", alpha=overlay_opacity, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Grad-CAM Heatmap Overlay (Model View)")
    return _figure_to_base64(fig)


def build_lime_explanation(image: Image.Image, num_samples: int) -> str:
    model = get_model()
    lime_image = generate_lime(model, image, transform, num_samples=num_samples)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(lime_image)
    ax.axis("off")
    ax.set_title("LIME Feature Importance")
    return _figure_to_base64(fig)
