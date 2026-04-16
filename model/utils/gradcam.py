import torch
import cv2
import numpy as np

class GradCAM:

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer

        self.gradients = None
        self.activations = None

        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate(self, image_tensor):

        output = self.model(image_tensor)

        pred = torch.argmax(output)

        self.model.zero_grad()
        output[0, pred].backward()

        gradients = self.gradients[0]
        activations = self.activations[0]

        weights = torch.mean(gradients, dim=(1,2))

        cam = torch.zeros(activations.shape[1:])

        for i,w in enumerate(weights):
            cam += w * activations[i]

        cam = torch.relu(cam)
        cam = cam.detach().numpy()

        cam = cv2.resize(cam,(224,224))
        cam = (cam - cam.min())/(cam.max()-cam.min())

        return cam