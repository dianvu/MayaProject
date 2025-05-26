import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Add project root to path (going up one level from features folder)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load the data
df = pd.read_csv(os.path.join(project_root, 'data/user_monthly_stats.csv'))

# Function to prepare features for clustering
def prepare_features(data, months):
    # Select relevant features for clustering
    features = [
        'spend_count',
        'cash_in_count',
        'total_spend',
        'total_cash_in'
    ]
    
    # Filter data for specified months
    monthly_data = data[data['month'].isin(months)]
    
    # Group by user_id and calculate mean of features
    user_features = monthly_data.groupby('user_id')[features].mean()
    
    # Scale the features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(user_features)
    
    return user_features, scaled_features

# Set the month to analyze
month_to_analyze = 4

# Prepare training data for the specified month
data_features, data_scaled = prepare_features(df, [month_to_analyze])

# Find optimal number of clusters using silhouette score
silhouette_scores = []
K = range(2, 11)
for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(data_scaled)
    score = silhouette_score(data_scaled, kmeans.labels_)
    silhouette_scores.append(score)

# Create output directory for results
output_dir = os.path.join(project_root, 'clustering')
os.makedirs(output_dir, exist_ok=True)

# Plot silhouette scores
plt.figure(figsize=(10, 6))
plt.plot(K, silhouette_scores, 'bo-')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score vs Number of Clusters')
plt.savefig(os.path.join(output_dir, f'silhouette_scores_month{month_to_analyze}.png'))
plt.close()

# Get optimal number of clusters
optimal_k = K[np.argmax(silhouette_scores)]
print(f"Optimal number of clusters: {optimal_k}")

# Train final model with optimal k
final_model = KMeans(n_clusters=optimal_k, random_state=42)
final_model.fit(data_scaled)

# Get cluster assignments for the data
data_clusters = final_model.predict(data_scaled)

# Analyze cluster characteristics
def analyze_clusters(features, clusters, title, month):
    # Add cluster assignments to features
    features_with_clusters = features.copy()
    features_with_clusters['cluster'] = clusters
    
    # Calculate cluster statistics
    cluster_stats = features_with_clusters.groupby('cluster').agg({
        'spend_count': ['mean'],
        'cash_in_count': ['mean'],
        'total_spend': ['mean'],
        'total_cash_in': ['mean']
    })
    
    # Format the statistics with 2 decimal places
    pd.set_option('display.float_format', lambda x: '%.2f' % x)
    
    # Save cluster statistics to a file
    stats_file = os.path.join(output_dir, f'{title.lower().replace(" ", "_")}_stats_month{month}.txt')
    with open(stats_file, 'w') as f:
        f.write(f"{title} Cluster Statistics (Month {month}):\n")
        f.write(str(cluster_stats))
    
    print(f"\nCluster statistics saved to: {stats_file}")
    
    # Visualize clusters
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        features['spend_count'],
        features['total_spend'],
        c=clusters,
        cmap='viridis'
    )
    plt.xlabel('Number of Spend Transactions')
    plt.ylabel('Total Spend Amount')
    plt.title(f'{title} - Transaction Patterns (Month {month})')
    plt.colorbar(scatter, label='Cluster')
    plt.savefig(os.path.join(output_dir, f'{title.lower().replace(" ", "_")}_month{month}.png'))
    plt.close()

# Analyze training and test clusters
analyze_clusters(data_features, data_clusters, "Clusters", month_to_analyze)