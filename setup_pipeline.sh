#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p /datasets/
mkdir -p /data/
mkdir -p /outputs/

# Inform user about Kaggle API key
echo "Please ensure your kaggle.json is in ~/.kaggle/kaggle.json"
echo "You can run: mkdir -p ~/.kaggle && cp kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json"

# Run the pipeline
# python main.py
