import os
import shutil
import random
import logging
import argparse
from utils import ensure_dir, setup_logging

setup_logging()

def split_dataset(src_dir, dest_dir, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42):
    random.seed(seed)
    
    classes = [d for d in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, d))]
    
    for cls in classes:
        cls_dir = os.path.join(src_dir, cls)
        images = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        random.shuffle(images)
        
        n = len(images)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        train_images = images[:n_train]
        val_images = images[n_train:n_train+n_val]
        test_images = images[n_train+n_val:]
        
        for split, split_images in [('train', train_images), ('val', val_images), ('test', test_images)]:
            split_dir = os.path.join(dest_dir, split, cls)
            ensure_dir(split_dir)
            for img in split_images:
                shutil.copy(os.path.join(cls_dir, img), os.path.join(split_dir, img))
        
        logging.info(f"Class {cls}: {len(train_images)} train, {len(val_images)} val, {len(test_images)} test")

def main():
    parser = argparse.ArgumentParser(description="Split dataset into train/val/test.")
    parser.add_argument("--input-dir", required=True, help="Source directory")
    parser.add_argument("--output-dir", required=True, help="Destination directory")
    args = parser.parse_args()
    
    if os.path.exists(args.input_dir):
        logging.info(f"Splitting dataset from {args.input_dir} to {args.output_dir}...")
        split_dataset(args.input_dir, args.output_dir)
    else:
        logging.error(f"Source directory {args.input_dir} not found.")

if __name__ == "__main__":
    main()
