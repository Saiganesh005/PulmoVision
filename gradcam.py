import cv2
import numpy as np
import torch
import torch.nn.functional as F


class GradCAM:
    """Grad-CAM helper for convolutional target layers."""

    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None

        self._forward_handle = self.target_layer.register_forward_hook(self._save_activations)
        self._backward_handle = self.target_layer.register_full_backward_hook(self._save_gradients)

    def _save_activations(self, module, input_tensor, output_tensor):
        self.activations = output_tensor

    def _save_gradients(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def remove_hooks(self):
        self._forward_handle.remove()
        self._backward_handle.remove()

    def generate(self, logits: torch.Tensor, target_class: int) -> torch.Tensor:
        """Generate normalized CAM for a single-image batch."""
        if logits.ndim != 2 or logits.size(0) != 1:
            raise ValueError("Grad-CAM expects logits with shape [1, num_classes]")

        self.model.zero_grad(set_to_none=True)
        score = logits[0, target_class]
        score.backward(retain_graph=True)

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Failed to capture activations/gradients for Grad-CAM")

        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)

        cam = cam[0, 0]
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        return cam.detach()


def get_device(device: torch.device | str | None = None) -> torch.device:
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def find_last_conv_layer(model: torch.nn.Module) -> torch.nn.Module:
    """Find the last Conv2d layer (works for most CNN / hybrid backbones)."""
    last_conv = None
    for module in model.modules():
        if isinstance(module, torch.nn.Conv2d):
            last_conv = module
    if last_conv is None:
        raise ValueError("No Conv2d layer found in model for Grad-CAM")
    return last_conv


def overlay_heatmap_on_image(
    base_image_rgb: np.ndarray,
    heatmap_0_1: np.ndarray,
    alpha: float = 0.4,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create color heatmap and overlay image.

    Returns:
      heatmap_color_rgb, overlay_rgb
    """
    if base_image_rgb.dtype != np.uint8:
        base_image_rgb = np.clip(base_image_rgb, 0, 255).astype(np.uint8)

    h, w = base_image_rgb.shape[:2]
    heatmap_resized = cv2.resize(heatmap_0_1, (w, h))
    heatmap_uint8 = np.uint8(255 * np.clip(heatmap_resized, 0, 1))

    heatmap_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)

    overlay = cv2.addWeighted(base_image_rgb, 1 - alpha, heatmap_rgb, alpha, 0)
    return heatmap_rgb, overlay


def generate_gradcam_visualization(
    model: torch.nn.Module,
    image_tensor: torch.Tensor,
    class_names: list[str] | None = None,
    target_class: int | None = None,
    target_layer: torch.nn.Module | None = None,
    device: torch.device | str | None = None,
    overlay_alpha: float = 0.4,
) -> dict:
    """
    Generate Grad-CAM heatmap and overlay for a single test image.

    Args:
        model: Trained classification model.
        image_tensor: Tensor image [C,H,W] or [1,C,H,W] normalized for model input.
        class_names: Optional class names for readable labels.
        target_class: Optional class index for Grad-CAM target.
        target_layer: Optional conv layer; if None, last Conv2d is used.
        device: Optional torch device.
        overlay_alpha: Heatmap overlay blend ratio.

    Returns:
        dict with predicted label, target label, heatmap, and overlay image arrays.
    """
    target_device = get_device(device)
    model = model.to(target_device)
    model.eval()

    if image_tensor.ndim == 3:
        input_tensor = image_tensor.unsqueeze(0)
    elif image_tensor.ndim == 4 and image_tensor.size(0) == 1:
        input_tensor = image_tensor
    else:
        raise ValueError("image_tensor must have shape [C,H,W] or [1,C,H,W]")

    input_tensor = input_tensor.to(target_device)

    cam_layer = target_layer if target_layer is not None else find_last_conv_layer(model)
    grad_cam = GradCAM(model=model, target_layer=cam_layer)

    try:
        logits = model(input_tensor)
        pred_class = int(torch.argmax(logits, dim=1).item())
        cam_class = pred_class if target_class is None else int(target_class)

        cam = grad_cam.generate(logits=logits, target_class=cam_class)
        cam_np = cam.cpu().numpy()

        # Convert the model input image to a displayable RGB image (0-255)
        image_np = input_tensor[0].detach().cpu().permute(1, 2, 0).numpy()
        image_np = image_np - image_np.min()
        if image_np.max() > 0:
            image_np = image_np / image_np.max()
        image_rgb = np.uint8(image_np * 255)

        heatmap_rgb, overlay_rgb = overlay_heatmap_on_image(
            base_image_rgb=image_rgb,
            heatmap_0_1=cam_np,
            alpha=overlay_alpha,
        )

        if class_names is not None:
            predicted_label_name = class_names[pred_class]
            target_label_name = class_names[cam_class]
        else:
            predicted_label_name = f"class_{pred_class}"
            target_label_name = f"class_{cam_class}"

        return {
            "predicted_class_index": pred_class,
            "predicted_class_name": predicted_label_name,
            "target_class_index": cam_class,
            "target_class_name": target_label_name,
            "heatmap": cam_np,
            "heatmap_rgb": heatmap_rgb,
            "overlay_rgb": overlay_rgb,
        }
    finally:
        grad_cam.remove_hooks()
