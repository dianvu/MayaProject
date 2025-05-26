import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def create_visualizations(csv_path: str, output_dir: str):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    
    # Create figure with subplots for box plots
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Evaluation Metrics Distribution', fontsize=16)
    
    # 1. Box plot of confidence scores by component
    sns.boxplot(data=df, x='component', y='confidence', ax=axes[0])
    axes[0].set_title('Confidence Score Distribution')
    axes[0].set_xlabel('Component')
    axes[0].set_ylabel('Confidence Score')
    
    # 2. Box plot of similarity scores by component
    sns.boxplot(data=df, x='component', y='similarity_score', ax=axes[1])
    axes[1].set_title('Similarity Score Distribution')
    axes[1].set_xlabel('Component')
    axes[1].set_ylabel('Similarity Score')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'score_boxplots.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create violin plots
    plt.figure(figsize=(15, 6))
    plt.subplot(1, 2, 1)
    sns.violinplot(data=df, x='component', y='confidence')
    plt.title('Confidence Score Distribution')
    plt.xlabel('Component')
    plt.ylabel('Confidence Score')
    
    plt.subplot(1, 2, 2)
    sns.violinplot(data=df, x='component', y='similarity_score')
    plt.title('Similarity Score Distribution')
    plt.xlabel('Component')
    plt.ylabel('Similarity Score')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'score_violinplots.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations saved to {output_dir}")

if __name__ == "__main__":
    # Define paths
    csv_path = "evaluations/2025/March/all_evaluations.csv"
    output_dir = "evaluations/2025/March/visualizations"
    
    # Create visualizations
    create_visualizations(csv_path, output_dir) 