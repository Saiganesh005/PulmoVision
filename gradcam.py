import torch
import torch.nn.functional as F
import numpy as np
import cv2
import matplotlib.pyplot as plt
from torchvision import transforms
from PIL import Image
import os

# Ensure the best model is loaded
# 'model' is already loaded and potentially trained in dbe3612b
# If re-running this cell independently, ensure model is initialized and 'best_model.pth' exists.
model.load_state_dict(torch.load('best_model.pth'))
model.eval() # Set model to evaluation mode

# --- Grad-CAM Implementation ---
class GradCAM:
    def __init__(self, model, target_layer_name):
        self.model = model
        self.model.eval()
        self.feature_map = None
        self.gradient = None
        self.target_layer_name = target_layer_name

        self._register_hooks()

    def _register_hooks(self):
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                module.register_forward_hook(self._save_feature_map)
                module.register_full_backward_hook(self._save_gradient)
                print(f"Registered hooks for target layer: {name}")
                return
        raise ValueError(f"Target layer '{self.target_layer_name}' not found in model.")

    def _save_feature_map(self, module, input, output):
        # Feature maps are the output of the layer
        self.feature_map = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        # Gradients are grad_output[0]
        self.gradient = grad_output[0].detach()

    def __call__(self, input_tensor, target_category=None):
        # Clear previous hooks data
        self.feature_map = None
        self.gradient = None

        # Forward pass
        output = self.model(input_tensor)
        
        if target_category is None:
            target_category = output.argmax(dim=1) # Get the predicted class

        # Zero gradients
        self.model.zero_grad()

        # Backward pass for the target category
        one_hot_output = torch.zeros_like(output, device=input_tensor.device)
        # Ensure target_category is a tensor if it's an int, for correct indexing
        if isinstance(target_category, int):
            target_category = torch.tensor([target_category], device=input_tensor.device)
        
        # Populate one_hot_output for the target category
        for i, category_idx in enumerate(target_category):
            one_hot_output[i, category_idx] = 1.0

        # Perform backward pass
        # retain_graph=True is important if you plan to do multiple backward passes
        # or if parts of the graph are needed later, e.g., for other Grad-CAMs.
        # For a single Grad-CAM, it can be False if not needed.
        output.backward(gradient=one_hot_output, retain_graph=True)

        if self.feature_map is None or self.gradient is None:
            raise RuntimeError("Feature map or gradient was not captured. Check target layer name and model execution.")

        # Global average pooling of gradients
        # For simplicity, if batch size > 1, we'll process the first image in the batch
        if input_tensor.shape[0] > 1:
            print("Warning: Grad-CAM processes one image at a time. Using the first image in the batch.")
            feature_map_batch = self.feature_map[0].unsqueeze(0) # Keep batch dim for adaptive_avg_pool2d
            gradient_batch = self.gradient[0].unsqueeze(0)
        else:
            feature_map_batch = self.feature_map
            gradient_batch = self.gradient

        # Compute weights for each feature map channel
        weights = F.adaptive_avg_pool2d(gradient_batch, 1) # Shape: (B, C, 1, 1)

        # Element-wise multiply weights with feature maps and sum across channels
        cam = (weights * feature_map_batch).sum(dim=1, keepdim=True) # Shape: (B, 1, H, W)
        cam = F.relu(cam) # Apply ReLU to only keep positive contributions

        # Normalize heatmap per image in batch (if batch size > 1)
        heatmaps_np = []
        for i in range(cam.shape[0]):
            single_cam = cam[i, 0]
            single_cam = single_cam - single_cam.min()
            if single_cam.max() == 0:
                heatmaps_np.append(None) # Handle case where all cam values are zero
            else:
                single_cam = single_cam / single_cam.max()
                heatmaps_np.append(single_cam.cpu().numpy())

        return heatmaps_np[0] if len(heatmaps_np) == 1 else heatmaps_np # Return list if batch, else single item

# --- Find a suitable target layer for FastViT-T8 ---
# Iteratively find the last Conv2d layer in the 'stages' of the model.
# This is a common heuristic for CNN-based or hybrid models like FastViT.
target_layer_name = None
for name, module in model.named_modules():
    # Heuristic: look for the last Conv2d within the 'stages' part of the network.
    # For FastViT-T8, `stages.2.blocks.2.conv3` is a likely candidate.
    if 'stages' in name and isinstance(module, torch.nn.Conv2d):
        target_layer_name = name # Keep updating to get the last one

if target_layer_name is None:
    raise ValueError("Could not find a suitable Conv2d layer in 'stages' for Grad-CAM. Please inspect model architecture.")

print(f"Selected target layer for Grad-CAM: {target_layer_name}")

# Initialize Grad-CAM
grad_cam = GradCAM(model, target_layer_name)

# --- Select a sample image from the test set ---
# 'test_dataset' and 'class_names' are available from cell 'dbe3612b'
sample_idx = 0 # You can change this to any index in the test set
image_tensor, true_label_idx = test_dataset[sample_idx]
image_path = test_dataset.samples[sample_idx][0] # Get original image path for display

# Move to device and add batch dimension
input_tensor = image_tensor.unsqueeze(0).to(DEVICE)

# Get the predicted label for this image
with torch.no_grad():
    output = model(input_tensor)
    predicted_label_idx = output.argmax(dim=1).item()

true_label_name = class_names[true_label_idx]
predicted_label_name = class_names[predicted_label_idx]

print(f"\nProcessing image: {os.path.basename(image_path)}")
print(f"True Label: {true_label_name}")
print(f"Predicted Label: {predicted_label_name}")

# Generate Grad-CAM for the predicted class
heatmap = grad_cam(input_tensor, predicted_label_idx)

if heatmap is None:
    print("Could not generate Grad-CAM heatmap (e.g., all activations were zero).")
else:
    # --- Visualization ---
    # Convert input tensor to numpy image for display
    # Inverse normalize (undo ImageNet normalization)
    inv_normalize = transforms.Normalize(
        mean=[-0.485/0.229, -0.456/0.224, -0.406/0.225],
        std=[1/0.229, 1/0.224, 1/0.225]
    )
    # Permute to (H, W, C) for matplotlib and convert to numpy
    original_image_display = inv_normalize(image_tensor).permute(1, 2, 0).cpu().numpy()
    original_image_display = np.clip(original_image_display, 0, 1) # Ensure values are within valid image range (0-1)

    # Resize heatmap to original image size for overlay
    h, w = original_image_display.shape[:2]
    heatmap_resized = cv2.resize(heatmap, (w, h))
    heatmap_resized = np.uint8(255 * heatmap_resized) # Scale to 0-255 for cv2 colormap

    # Apply colormap to heatmap
    heatmap_colored = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB) # Convert BGR to RGB for matplotlib

    # Create a translucent overlay
    # Original image needs to be scaled to 0-255 for proper blending with heatmap_colored
    superimposed_img = heatmap_colored * 0.4 + (original_image_display * 255) * 0.6
    superimposed_img = np.uint8(np.clip(superimposed_img, 0, 255))

    plt.figure(figsize=(15, 7))
    plt.subplot(1, 3, 1)
    plt.imshow(original_image_display)
    plt.title(f"Original Image\nTrue: {true_label_name}, Pred: {predicted_label_name}")
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.imshow(superimposed_img)
    plt.title("Grad-CAM Overlay")
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(heatmap_resized, cmap='jet')
    plt.title("Grad-CAM Heatmap")
    plt.axis('off')

    plt.tight_layout()
    plt.show()