import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocess import get_transforms
from torch.utils.data import DataLoader
from torchvision import datasets

def get_dataloaders(data_dir, batch_size=32):
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val')
    
    train_dataset = datasets.ImageFolder(train_dir, transform=get_transforms(is_train=True))
    val_dataset = datasets.ImageFolder(val_dir, transform=get_transforms(is_train=False))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    return train_loader, val_loader, train_dataset.classes
