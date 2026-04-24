import torch
import torch.nn as nn


def get_training_device(device: torch.device | str | None = None) -> torch.device:
    """Resolve training device with CUDA fallback."""
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def train_classification_model(
    model: nn.Module,
    train_loader,
    optimizer: torch.optim.Optimizer,
    epochs: int,
    device: torch.device | str | None = None,
    criterion: nn.Module | None = None,
    use_amp: bool = True,
) -> tuple[nn.Module, dict]:
    """
    Train an image-classification model and track epoch training loss.

    Args:
        model: PyTorch model to train.
        train_loader: DataLoader yielding (images, labels).
        optimizer: Optimizer (e.g., Adam, SGD).
        epochs: Number of training epochs.
        device: Training device; auto-selects CUDA if available.
        criterion: Loss function (defaults to CrossEntropyLoss).
        use_amp: Enable mixed precision on CUDA for faster training/lower memory.

    Returns:
        trained_model, history where history['train_loss'] is a list of epoch losses.
    """
    if epochs <= 0:
        raise ValueError("epochs must be > 0")

    target_device = get_training_device(device)
    model = model.to(target_device)

    if criterion is None:
        criterion = nn.CrossEntropyLoss()

    scaler = torch.amp.GradScaler("cuda", enabled=use_amp and target_device.type == "cuda")

    history = {"train_loss": []}

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        total_samples = 0

        for images, labels in train_loader:
            images = images.to(target_device, non_blocking=True)
            labels = labels.to(target_device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast(
                device_type=target_device.type,
                enabled=use_amp and target_device.type == "cuda",
            ):
                outputs = model(images)  # Forward pass
                loss = criterion(outputs, labels)  # CrossEntropy loss calculation

            # Backpropagation + optimizer step
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            batch_size = labels.size(0)
            running_loss += loss.item() * batch_size
            total_samples += batch_size

        epoch_loss = running_loss / max(total_samples, 1)
        history["train_loss"].append(epoch_loss)
        print(f"Epoch [{epoch + 1}/{epochs}] - Train Loss: {epoch_loss:.4f}")

    return model, history
