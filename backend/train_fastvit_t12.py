import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from timm import create_model
import os

# --- Configuration ---
MODEL_NAME = "fastvit_t8"
OPTIMIZER = "AdamW"
LR = 3e-4
BATCH_SIZE = 8
EPOCHS = 10 # User specified 10-15 epochs, starting with 10
IMG_SIZE = 224 # User specified 224 (or 160 for speed)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Using device: {DEVICE}")

# --- Paths (assuming previous cells have been executed) ---
# The split dataset path from cell 41c5157c
split_dataset_base_path = "/content/datasplitting" # Corrected path to match cell 41c5157c output

train_dir = os.path.join(split_dataset_base_path, 'train')
val_dir = os.path.join(split_dataset_base_path, 'validation')
test_dir = os.path.join(split_dataset_base_path, 'test')

# Check if dataset directories exist
if not os.path.exists(train_dir):
    raise FileNotFoundError(f"Training directory not found: {train_dir}. Please ensure dataset splitting cell (41c5157c) has been executed.")
if not os.path.exists(val_dir):
    raise FileNotFoundError(f"Validation directory not found: {val_dir}. Please ensure dataset splitting cell (41c5157c) has been executed.")
if not os.path.exists(test_dir):
    raise FileNotFoundError(f"Test directory not found: {test_dir}. Please ensure dataset splitting cell (41c5157c) has been executed.")


# --- Data Transforms ---
# Basic transforms for training (with augmentation) and ImageNet normalization
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # ImageNet normalization
])

# Validation and test transforms (no augmentation) with ImageNet normalization
val_test_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- Datasets ---
train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
val_dataset = datasets.ImageFolder(val_dir, transform=val_test_transform)
test_dataset = datasets.ImageFolder(test_dir, transform=val_test_transform)

# --- Data Loaders ---
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2) # num_workers for faster loading
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

print(f"Number of classes: {len(train_dataset.classes)}")
print(f"Train dataset size: {len(train_dataset)}")
print(f"Validation dataset size: {len(val_dataset)}")
print(f"Test dataset size: {len(test_dataset)}")

# --- Model ---
# Ensure timm library is installed: !pip install timm
try:
    model = create_model(MODEL_NAME, pretrained=True, num_classes=len(train_dataset.classes))
    model = model.to(DEVICE)
    print(f"Model '{MODEL_NAME}' loaded successfully with {len(train_dataset.classes)} output classes.")
except Exception as e:
    print(f"Error loading model: {e}. Please ensure 'timm' is installed and model name '{MODEL_NAME}' is correct.")
    raise # Re-raise the exception to stop execution if model fails to load

# --- Loss Function and Optimizer ---
criterion = nn.CrossEntropyLoss()
if OPTIMIZER == "AdamW":
    optimizer = optim.AdamW(model.parameters(), lr=LR)
else:
    # Default to Adam if other optimizers are not explicitly handled
    optimizer = optim.Adam(model.parameters(), lr=LR)
print(f"Optimizer: {OPTIMIZER} with LR={LR}")

# --- Training Loop ---
print("Starting training...")
best_val_loss = float('inf')

# Lists to store metrics
train_losses = []
train_accuracies = []
val_losses = []
val_accuracies = []

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    correct_train = 0
    total_train = 0
    for i, (inputs, labels) in enumerate(train_loader):
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, predicted_train = torch.max(outputs.data, 1)
        total_train += labels.size(0)
        correct_train += (predicted_train == labels).sum().item()

    epoch_loss = running_loss / len(train_dataset)
    epoch_accuracy = 100 * correct_train / total_train
    train_losses.append(epoch_loss)
    train_accuracies.append(epoch_accuracy)
    print(f"Epoch {epoch+1}/{EPOCHS}, Train Loss: {epoch_loss:.4f}, Train Accuracy: {epoch_accuracy:.2f}%")

    # --- Validation ---
    model.eval() # Set model to evaluation mode
    val_running_loss = 0.0
    correct_val = 0
    total_val = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            val_running_loss += loss.item() * inputs.size(0)
            _, predicted_val = torch.max(outputs.data, 1)
            total_val += labels.size(0)
            correct_val += (predicted_val == labels).sum().item()

    val_loss = val_running_loss / len(val_dataset)
    val_accuracy = 100 * correct_val / total_val
    val_losses.append(val_loss)
    val_accuracies.append(val_accuracy)
    print(f"Validation Loss: {val_loss:.4f}, Validation Accuracy: {val_accuracy:.2f}%")

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), 'best_model.pth') # Save the model state_dict
        print("Saved best model based on validation loss!")

print("Training complete.")

# --- Evaluate on Test Set ---
# Load the best model weights before evaluating on the test set
model.load_state_dict(torch.load('best_model.pth'))
model.eval() # Set model to evaluation mode
test_loss = 0.0
correct_test = 0
total_test = 0

# Variables to store all predictions and labels for confusion matrix and classification report
all_labels = []
all_predictions = []

with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        test_loss += loss.item() * inputs.size(0)
        _, predicted_test = torch.max(outputs.data, 1)
        total_test += labels.size(0)
        correct_test += (predicted_test == labels).sum().item()

        all_labels.extend(labels.cpu().numpy())
        all_predictions.extend(predicted_test.cpu().numpy())

final_test_loss = test_loss / len(test_dataset)
final_test_accuracy = 100 * correct_test / total_test
print(f"\nFinal Test Loss: {final_test_loss:.4f}, Final Test Accuracy: {final_test_accuracy:.2f}%")

# Make class_names available for subsequent cells
class_names = train_dataset.classes