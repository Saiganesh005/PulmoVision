import os
import logging
from PIL import Image
from utils import setup_logging

try:
    from torchvision import transforms
    HAS_TORCHVISION = True
except ImportError:
    logging.warning("torchvision not found. Preprocessing will be limited.")
    HAS_TORCHVISION = False

setup_logging()

def preprocess_image(img_path, target_size=(224, 224)):
    try:
        img = Image.open(img_path).convert('RGB')
        img = img.resize(target_size)
        return img
    except Exception as e:
        logging.error(f"Error preprocessing {img_path}: {e}")
        return None

def get_transforms(is_train=True):
    if not HAS_TORCHVISION:
        # Return a dummy object that can be called but does nothing
        return lambda x: x
        
    if is_train:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomRotation(15),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

if __name__ == "__main__":
    logging.info("Preprocessing and Augmentation logic defined.")

