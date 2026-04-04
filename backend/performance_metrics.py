import torch
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from timm import create_model
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import os
import json

# --- Configuration ---
MODEL_NAME = "fastvit_t8"
BATCH_SIZE = 32
IMG_SIZE = 224
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Paths based on previous dataset splitting and training
TEST_DIR = "/content/datasplitting/test"
CHECKPOINT_PATH = "best_model.pth"

def calculate_specificity(cm):
    """
    Calculates the specificity for each class given a confusion matrix.
    Returns the macro-average specificity and a list of specificities per class.
    """
    specificities = []
    num_classes = cm.shape[0]
    
    for i in range(num_classes):
        TP = cm[i, i]
        FP = np.sum(cm[:, i]) - TP
        FN = np.sum(cm[i, :]) - TP
        TN = np.sum(cm) - (TP + FP + FN)
        
        # Specificity = TN / (TN + FP)
        if (TN + FP) > 0:
            specificity = TN / (TN + FP)
        else:
            specificity = 0.0
            
        specificities.append(specificity)
        
    # Return macro average and individual class specificities
    return np.mean(specificities), specificities

def main():
    print(f"Using device: {DEVICE}")
    
    if not os.path.exists(TEST_DIR):
        print(f"Error: Test directory not found at {TEST_DIR}")
        print("Please ensure the dataset splitting script has been executed.")
        return
        
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"Error: Model checkpoint not found at {CHECKPOINT_PATH}")
        print("Please ensure the model has been trained and saved.")
        return

    # --- Data Transforms ---
    # Same normalization used during training
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # --- Dataset & Loader ---
    test_dataset = datasets.ImageFolder(TEST_DIR, transform=transform)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    class_names = test_dataset.classes

    print(f"Loaded test dataset with {len(test_dataset)} images across {len(class_names)} classes.")

    # --- Model Initialization ---
    print(f"Loading {MODEL_NAME} model from {CHECKPOINT_PATH}...")
    model = create_model(MODEL_NAME, pretrained=False, num_classes=len(class_names))
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    all_preds = []
    all_labels = []

    print("Running inference on the test set. This may take a moment...")
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(DEVICE)
            outputs = model(inputs)
            preds = outputs.argmax(dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    # --- Calculate Metrics ---
    # Multiply by 100 to get percentages
    acc = accuracy_score(all_labels, all_preds) * 100
    prec = precision_score(all_labels, all_preds, average='weighted', zero_division=0) * 100
    rec = recall_score(all_labels, all_preds, average='weighted', zero_division=0) * 100
    f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0) * 100

    # Confusion matrix for specificity
    cm = confusion_matrix(all_labels, all_preds)
    mean_spec, class_specs = calculate_specificity(cm)
    mean_spec *= 100 # Convert macro average to percentage

    # --- Output Results ---
    print("\n" + "="*50)
    print(" OVERALL PERFORMANCE METRICS (Percentages)")
    print("="*50)
    print(f" Accuracy    : {acc:.2f}%")
    print(f" Precision   : {prec:.2f}%")
    print(f" Recall      : {rec:.2f}%")
    print(f" F1 Score    : {f1:.2f}%")
    print(f" Specificity : {mean_spec:.2f}%")
    print("="*50)

    print("\n--- Class-wise Specificity ---")
    for name, spec in zip(class_names, class_specs):
        print(f" {name.ljust(20)} : {spec * 100:.2f}%")
        
    # Save metrics to a JSON file for easy access later
    metrics_dict = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1_score": float(f1),
        "specificity_macro_avg": float(mean_spec),
        "class_specificities": {name: float(spec * 100) for name, spec in zip(class_names, class_specs)}
    }
    
    with open("performance_results.json", "w") as f:
        json.dump(metrics_dict, f, indent=4)
    print("\nMetrics saved to performance_results.json")

if __name__ == "__main__":
    main()
