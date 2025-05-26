import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
df = pd.read_csv('data/user_monthly_stats.csv')

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

# Prepare training data (months 1-4)
train_features, train_scaled = prepare_features(df, [1, 2, 3, 4])

# Find optimal number of clusters using silhouette score
silhouette_scores = []
K = range(2, 11)
for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(train_scaled)
    score = silhouette_score(train_scaled, kmeans.labels_)
    silhouette_scores.append(score)

# Plot silhouette scores
plt.figure(figsize=(10, 6))
plt.plot(K, silhouette_scores, 'bo-')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score vs Number of Clusters')
plt.savefig('silhouette_scores.png')
plt.close()

# Get optimal number of clusters
optimal_k = K[np.argmax(silhouette_scores)]
print(f"Optimal number of clusters: {optimal_k}")

# Train final model with optimal k
final_model = KMeans(n_clusters=optimal_k, random_state=42)
final_model.fit(train_scaled)

# Get cluster assignments for training data
train_clusters = final_model.predict(train_scaled)

# Prepare test data (month 4)
test_features, test_scaled = prepare_features(df, [4])

# Get cluster assignments for test data
test_clusters = final_model.predict(test_scaled)

# Analyze cluster characteristics
def analyze_clusters(features, clusters, title):
    # Add cluster assignments to features
    features_with_clusters = features.copy()
    features_with_clusters['cluster'] = clusters
    
    # Calculate cluster statistics
    cluster_stats = features_with_clusters.groupby('cluster').agg({
        'spend_count': ['mean', 'std'],
        'cash_in_count': ['mean', 'std'],
        'total_spend': ['mean', 'std'],
        'total_cash_in': ['mean', 'std']
    })
    
    print(f"\n{title} Cluster Statistics:")
    print(cluster_stats)
    
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
    plt.title(f'{title} - Transaction Patterns by Cluster')
    plt.colorbar(scatter, label='Cluster')
    plt.savefig(f'{title.lower().replace(" ", "_")}_clusters.png')
    plt.close()

# Analyze training and test clusters
analyze_clusters(train_features, train_clusters, "Training")
analyze_clusters(test_features, test_clusters, "Test")

# Calculate cluster stability
def calculate_cluster_stability(train_clusters, test_clusters):
    # Create a mapping of user IDs to their cluster assignments
    train_mapping = dict(zip(train_features.index, train_clusters))
    test_mapping = dict(zip(test_features.index, test_clusters))
    
    # Find common users
    common_users = set(train_mapping.keys()) & set(test_mapping.keys())
    
    # Calculate stability
    stable_assignments = sum(1 for user in common_users 
                           if train_mapping[user] == test_mapping[user])
    stability = stable_assignments / len(common_users) if common_users else 0
    
    print(f"\nCluster Stability: {stability:.2%}")

calculate_cluster_stability(train_clusters, test_clusters) 