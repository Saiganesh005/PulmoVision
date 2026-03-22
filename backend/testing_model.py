from __future__ import annotations

import argparse
from pathlib import Path

import timm
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from dataloader import get_dataloaders


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test a trained FastViT model with a local image file.")
    parser.add_argument("--image-path", type=Path, default=None, help="Path to local image file.")
    parser.add_argument("--model-name", type=str, default="fastvit_t12", help="timm model name.")
    parser.add_argument("--checkpoint", type=Path, default=Path("fastvit_t12_model.pth"), help="Path to model checkpoint.")
    parser.add_argument("--data-dir", type=str, default="/content/Preprocess_data", help="Dataset path used to infer class names.")
    return parser.parse_args()


def upload_image_if_needed(image_path: Path | None) -> Path:
    """Return an image path, optionally uploading from local drive in Google Colab."""
    if image_path is not None:
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        return image_path

    try:
        from google.colab import files  # type: ignore
    except ImportError as exc:  # non-Colab environments
        raise ValueError("Provide --image-path when not running in Google Colab.") from exc

    uploaded = files.upload()
    if not uploaded:
        raise ValueError("No file uploaded.")

    uploaded_name = next(iter(uploaded))
    return Path(uploaded_name)


def load_model(model_name: str, checkpoint: Path, num_classes: int, device: torch.device) -> torch.nn.Module:
    if not checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")

    model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
    model.load_state_dict(torch.load(checkpoint, map_location=device))
    model.to(device)
    model.eval()
    return model


def predict_image(
    model: torch.nn.Module,
    image_path: Path,
    class_names: list[str],
    device: torch.device,
) -> tuple[str, float]:
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )

    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probabilities = F.softmax(outputs, dim=1)
        confidence, predicted_index = probabilities.max(dim=1)

    predicted_class = class_names[predicted_index.item()]
    return predicted_class, confidence.item() * 100.0


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    image_path = upload_image_if_needed(args.image_path)

    _, _, class_names = get_dataloaders(data_dir=args.data_dir)

    model = load_model(
        model_name=args.model_name,
        checkpoint=args.checkpoint,
        num_classes=len(class_names),
        device=device,
    )

    predicted_class, confidence = predict_image(model, image_path, class_names, device)

    print(f"Image: {image_path}")
    print(f"Predicted Class: {predicted_class}")
    print(f"Confidence: {confidence:.2f}%")


if __name__ == "__main__":
    main()
