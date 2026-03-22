# Deep Learning Pipeline for Medical Image Classification

This pipeline is designed to run within the Google AI Studio Code Space. It downloads medical datasets, splits them, preprocesses images, trains a Fast Vision Transformer (FastViT) model, and evaluates the performance.

## Prerequisites

1.  **Kaggle API Key**: You must provide your `kaggle.json` file.
    -   Place it in `~/.kaggle/kaggle.json` or upload it to the workspace.
    -   Run `mkdir -p ~/.kaggle && cp kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json`
    -   **Kaggle Hub Integration**: The pipeline now uses `kagglehub` for faster and more reliable dataset downloads.
    -   **Model Management**: You can also download pretrained models from Kaggle Hub and upload your trained models using `kagglehub.model_download` and `kagglehub.model_upload`.

2.  **Python Dependencies**:
    -   Install the required libraries: `pip install -r requirements.txt`

## Running the Pipeline

You can run the entire pipeline with a single command:

```bash
python main.py
```

Alternatively, you can run each step individually:

1.  **Download**: `python download.py`
2.  **Split**: `python split.py`
3.  **Train**: `python train.py`
4.  **Evaluate**: `python evaluate.py`
5.  **Inference**: `python inference.py`
6.  **Upload**: `python upload_to_kaggle.py` (requires handle configuration)

## Colab Export & Acquisition

For handling large datasets (like the 45GB NIH Chest X-ray), you can use the **Finalise & Export to Colab** feature in the web interface.

1.  Navigate to the **Download Dataset** or **Dataset Management** module.
2.  Select your desired datasets and configuration.
3.  Click **Finalise & Export to Colab**.
4.  This will download `medical_dataset_acquisition.ipynb` and open Google Colab.
5.  Upload the notebook to Colab and run it to leverage high-performance cloud storage and compute.

## Outputs

All results are saved in the `/outputs/` directory:
-   `model.pth`: The trained model weights.
-   `metrics.json`: Accuracy, Precision, Recall, and F1-score.
-   `confusion_matrix.png`: A heatmap of the confusion matrix.
-   `pipeline.log`: Detailed logs of the execution.

## Note on Datasets

-   The **NIH Chest X-ray Dataset** is approximately 45GB. By default, it is skipped in `download.py` to avoid exceeding disk limits. You can enable it by modifying the `DATASETS` dictionary in `download.py`.
-   The pipeline uses **FastViT (T12)** by default. If it fails, it falls back to **ResNet18**.
