import torch
from sklearn.metrics import classification_report


def get_test_device(device: torch.device | str | None = None) -> torch.device:
    """Resolve the device for model testing."""
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def test_model_on_unseen_dataset(
    model: torch.nn.Module,
    test_loader,
    class_names: list[str] | None = None,
    device: torch.device | str | None = None,
    print_examples: int = 20,
) -> dict:
    """
    Test a trained model on an unseen test DataLoader.

    Args:
        model: Trained PyTorch model.
        test_loader: DataLoader providing (images, labels).
        class_names: Optional list of class names indexed by class id.
        device: Optional evaluation device.
        print_examples: Number of prediction examples to display.

    Returns:
        Dict containing predicted labels, mapped class names, and classification report.
    """
    target_device = get_test_device(device)
    model = model.to(target_device)

    # No training during testing
    model.eval()

    all_true = []
    all_pred = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(target_device, non_blocking=True)
            labels = labels.to(target_device, non_blocking=True)

            outputs = model(images)
            preds = torch.argmax(outputs, dim=1)

            all_true.extend(labels.cpu().tolist())
            all_pred.extend(preds.cpu().tolist())

    if class_names is None:
        class_count = max(max(all_true, default=0), max(all_pred, default=0)) + 1
        class_names = [f"class_{idx}" for idx in range(class_count)]

    predicted_class_names = [class_names[index] for index in all_pred]
    true_class_names = [class_names[index] for index in all_true]

    # Build a complete classification report (precision, recall, f1-score, support)
    report_dict = classification_report(
        all_true,
        all_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
        output_dict=True,
    )

    report_text = classification_report(
        all_true,
        all_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
    )

    print("\n=== Classification Report (Test Set) ===")
    print(report_text)

    sample_count = min(print_examples, len(all_pred))
    if sample_count > 0:
        print("\n=== Sample Predictions ===")
        for idx in range(sample_count):
            print(
                f"Sample {idx + 1}: "
                f"true={true_class_names[idx]} ({all_true[idx]}) | "
                f"pred={predicted_class_names[idx]} ({all_pred[idx]})"
            )

    return {
        "true_labels": all_true,
        "predicted_labels": all_pred,
        "true_class_names": true_class_names,
        "predicted_class_names": predicted_class_names,
        "classification_report": report_dict,
        "classification_report_text": report_text,
    }
