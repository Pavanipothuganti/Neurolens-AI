import torch
import torch.nn as nn
from torchvision import models

def load_model(model_path):

    model = models.resnet18(weights=None)

    model.fc = nn.Sequential(
        nn.Linear(512,256),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(256,4)
    )

    model.load_state_dict(torch.load(model_path, map_location="cpu"))

    model.eval()

    return model