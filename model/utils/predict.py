import torch
import numpy as np
from PIL import Image
from torchvision import transforms

classes = [
    "No Impairment",
    "Very Mild Impairment",
    "Mild Impairment",
    "Moderate Impairment"
]

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485,0.456,0.406],
        std=[0.229,0.224,0.225]
    )
])

def predict_image(model,image):

    image = image.convert("RGB")

    img = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model(img)
        probs = torch.softmax(output,dim=1)

    pred = torch.argmax(probs,dim=1).item()

    return classes[pred],probs.numpy()[0]