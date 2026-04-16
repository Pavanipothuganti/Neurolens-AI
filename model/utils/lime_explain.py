import numpy as np
from lime import lime_image
import torch
from PIL import Image

def generate_lime(model, image, transform, num_samples=1000):

    explainer = lime_image.LimeImageExplainer()

    image_np = np.array(image)

    def batch_predict(images):

        model.eval()

        batch = torch.stack([
            transform(Image.fromarray(img)) for img in images
        ])

        with torch.no_grad():
            preds = model(batch)
            probs = torch.softmax(preds, dim=1)

        return probs.numpy()

    explanation = explainer.explain_instance(
        image_np,
        batch_predict,
        top_labels=1,
        hide_color=0,
        num_samples=num_samples
    )

    temp, mask = explanation.get_image_and_mask(
        explanation.top_labels[0],
        positive_only=True,
        num_features=8,
        hide_rest=False
    )

    base_image = temp.astype(np.float32) / 255.0
    overlay = np.zeros_like(base_image)
    overlay[..., 0] = 1.0
    overlay[..., 1] = 0.3

    mask_bool = mask > 0

    # Dim regions with low importance so selected superpixels stand out clearly.
    result = base_image.copy()
    result[~mask_bool] *= 0.35
    result[mask_bool] = (0.45 * base_image[mask_bool]) + (0.55 * overlay[mask_bool])

    return np.clip(result, 0.0, 1.0)
