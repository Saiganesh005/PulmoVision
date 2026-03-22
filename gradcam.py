import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import timm
from preprocess import get_transforms

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        def save_gradient(module, grad_input, grad_output):
            self.gradients = grad_output[0]
            
        def save_activation(module, input, output):
            self.activations = output
            
        self.target_layer.register_forward_hook(save_activation)
        self.target_layer.register_full_backward_hook(save_gradient)
        
    def generate_heatmap(self, input_tensor, class_idx=None):
        self.model.zero_grad()
        output = self.model(input_tensor)
        
        if class_idx is None:
            class_idx = torch.argmax(output)
            
        output[0, class_idx].backward()
        
        gradients = self.gradients
        activations = self.activations
        
        b, c, h, w = gradients.shape
        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)
        heatmap = torch.sum(weights * activations, dim=1).squeeze()
        
        heatmap = F.relu(heatmap)
        heatmap /= torch.max(heatmap)
        
        return heatmap.cpu().detach().numpy()

def save_gradcam(img_path, model_path="/outputs/model.pth", model_name='fastvit_t12', output_path="/outputs/gradcam.png"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load model
    model = timm.create_model(model_name, pretrained=False, num_classes=4) # Example classes
    model.load_state_dict(torch.load(model_path))
    model = model.to(device)
    model.eval()
    
    # Target layer for Grad-CAM (example for FastViT)
    # Note: This layer name might vary depending on the model architecture
    try:
        target_layer = model.stages[-1].blocks[-1]
    except:
        target_layer = model.conv_head # Fallback
        
    grad_cam = GradCAM(model, target_layer)
    
    # Load and transform image
    img = Image.open(img_path).convert('RGB')
    transform = get_transforms(is_train=False)
    input_tensor = transform(img).unsqueeze(0).to(device)
    
    heatmap = grad_cam.generate_heatmap(input_tensor)
    
    # Superimpose heatmap on original image
    img_np = np.array(img.resize((224, 224)))
    heatmap = cv2.resize(heatmap, (224, 224))
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    
    superimposed_img = heatmap * 0.4 + img_np
    cv2.imwrite(output_path, superimposed_img)
    
    logging.info(f"Grad-CAM visualization saved to {output_path}")

if __name__ == "__main__":
    import logging
    from utils import setup_logging
    setup_logging()
    
    img_path = "/data/test/covid/COVID-1.png"
    if os.path.exists(img_path) and os.path.exists("/outputs/model.pth"):
        save_gradcam(img_path)
    else:
        logging.warning("Image or model not found. Skip Grad-CAM.")
