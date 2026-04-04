import matplotlib.pyplot as plt
import seaborn as sns

print(f"Final Test Loss: {final_test_loss:.4f}")
print(f"Final Test Accuracy: {final_test_accuracy:.2f}%")


# Visualize the Confusion Matrix
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix on Test Set')
plt.show()
from sklearn.metrics import classification_report
import numpy as np

# Assuming all_labels and all_predictions are available from the test evaluation loop
# And class_names contains the list of class names in the correct order

# Get the unique labels present in the true labels (all_labels)
unique_labels_in_data = np.unique(all_labels)

# Filter class_names to only include those that are actually present in the data
target_names_for_report = [class_names[label_idx] for label_idx in sorted(unique_labels_in_data)]

print("\nClassification Report:")
print(classification_report(all_labels, all_predictions,
                            labels=sorted(unique_labels_in_data), # Explicitly define the labels to consider
                            target_names=target_names_for_report)) # Use the filtered class names
from sklearn.metrics import confusion_matrix
import numpy as np

# Assuming `cm` (confusion matrix) and `class_names` are available from previous executions

def calculate_specificity(cm):
    specificity_scores = {}
    num_classes = cm.shape[0]

    for i in range(num_classes):
        # True Positives (TP): Diagonal element for class i
        TP = cm[i, i]

        # False Positives (FP): Sum of column i excluding TP
        FP = np.sum(cm[:, i]) - TP

        # False Negatives (FN): Sum of row i excluding TP
        FN = np.sum(cm[i, :]) - TP

        # True Negatives (TN): Sum of all elements excluding row i and column i
        TN = np.sum(cm) - (TP + FP + FN)

        # Specificity = TN / (TN + FP)
        if (TN + FP) == 0:
            specificity = 0.0 # Avoid division by zero, or handle as NaN/None
        else:
            specificity = TN / (TN + FP)
        specificity_scores[class_names[i]] = specificity
    return specificity_scores

specificities = calculate_specificity(cm)

print("\n--- Performance Metrics Summary ---")
print(f"Overall Test Accuracy: {final_test_accuracy:.2f}%")
print("\nSpecificity per class:")
for class_name, spec in specificities.items():
    print(f"  {class_name}: {spec:.2f}")

# Reiterate overall precision, recall, f1-score if available from a previous report
# For this example, we'll re-run a simplified classification report to get averages
# or you can look at the output of the previous classification_report

# Note: Full classification_report output already provided detailed precision, recall, f1-score.
# This part is just to summarize if needed, otherwise refer to the previous output.