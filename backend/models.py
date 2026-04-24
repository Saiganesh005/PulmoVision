import torch
import torch.nn as nn
import timm
from torchvision import models
from torchvision.models import ResNet18_Weights


def get_device() -> torch.device:
    """Return GPU device if available, else CPU."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_resnet18(num_classes: int, pretrained: bool = True, device: torch.device | None = None) -> nn.Module:
    """
    Build a ResNet18 model for classification.

    Args:
        num_classes: Number of target classes.
        pretrained: Use ImageNet pretrained weights if True.
        device: Optional target device. If None, auto-select CUDA/CPU.

    Returns:
        ResNet18 model moved to target device.
    """
    if num_classes <= 0:
        raise ValueError("num_classes must be > 0")

    weights = ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    target_device = device or get_device()
    return model.to(target_device)


def build_vit(
    num_classes: int,
    pretrained: bool = True,
    model_name: str = "vit_base_patch16_224",
    device: torch.device | None = None,
) -> nn.Module:
    """
    Build a Vision Transformer (or FastViT) model using timm.

    Args:
        num_classes: Number of target classes.
        pretrained: Use pretrained weights if available.
        model_name: timm model name. Examples:
            - "vit_base_patch16_224"
            - "vit_small_patch16_224"
            - "fastvit_t8.apple_dist_in1k"
            - "fastvit_t12.apple_dist_in1k"
        device: Optional target device. If None, auto-select CUDA/CPU.

    Returns:
        timm model moved to target device.
    """
    if num_classes <= 0:
        raise ValueError("num_classes must be > 0")

    model = timm.create_model(
        model_name,
        pretrained=pretrained,
        num_classes=num_classes,
    )

    target_device = device or get_device()
    return model.to(target_device)


def build_classification_models(
    num_classes: int,
    pretrained: bool = True,
    vit_model_name: str = "vit_base_patch16_224",
    device: torch.device | None = None,
) -> tuple[nn.Module, nn.Module, torch.device]:
    """
    Build both required models:
      1) CNN (ResNet18)
      2) Transformer (ViT/FastViT)

    Returns:
        (resnet18_model, vit_or_fastvit_model, device)
    """
    target_device = device or get_device()

    resnet18_model = build_resnet18(
        num_classes=num_classes,
        pretrained=pretrained,
        device=target_device,
    )

    vit_model = build_vit(
        num_classes=num_classes,
        pretrained=pretrained,
        model_name=vit_model_name,
        device=target_device,
    )

    return resnet18_model, vit_model, target_device


if __name__ == "__main__":
    NUM_CLASSES = 4

    resnet18_model, vit_model, device = build_classification_models(
        num_classes=NUM_CLASSES,
        pretrained=True,
        vit_model_name="vit_base_patch16_224",  # switch to FastViT if needed
    )

    print(f"Device: {device}")
    print(f"ResNet18 classifier out_features: {resnet18_model.fc.out_features}")
    print(f"ViT/FastViT model ready: {type(vit_model).__name__}")
