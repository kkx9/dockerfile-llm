from collections import Counter
import cupy as cp
import logging
import numpy as np
from tqdm import tqdm
from cuml.cluster import DBSCAN
from cuml.neighbors import NearestNeighbors
from cuml.metrics.cluster import silhouette_score
import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
# from sklearn.metrics import calinski_harabasz_score, silhouette_score


EPS_VALUE = 5.5
logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.DEBUG)

min_samples_values = [769]

def plot_k_distance(params, samples, k):
    # Fit NearestNeighbors model
    neighbors = NearestNeighbors(n_neighbors=k)
    neighbors_fit = neighbors.fit(samples)
    distances, indices = neighbors_fit.kneighbors(samples)
    
    # Sort distances
    distances = np.sort(distances[:, k-1], axis=0)
    
    # Plot distances
    plt.figure(figsize=(10, 6))
    plt.plot(distances)
    plt.title('K-Distance Graph')
    plt.xlabel('Data Points sorted by distance')
    plt.ylabel(f'{k}-th Nearest Neighbor Distance')
    plt.grid(True)
    plt.savefig(f"{params['task_name']}.jpg")


def calinski_harabasz_score_gpu(X, labels):
    n_samples, n_features = X.shape
    n_clusters = len(cp.unique(labels)) - 1

    global_center = cp.mean(X, axis=0)

    W_k = cp.zeros((n_features, n_features), dtype=cp.float32)
    B_k = cp.zeros((n_features, n_features), dtype=cp.float32)

    for i in range(n_clusters):
        cluster_points = X[labels == i]
        cluster_center = cp.mean(cluster_points, axis=0)
        W_k += cp.dot((cluster_points - cluster_center).T, (cluster_points - cluster_center))
        cluster_size = cluster_points.shape[0]
        B_k += cluster_size * cp.outer(cluster_center - global_center, cluster_center - global_center)
    ch_score = (cp.trace(B_k) / cp.trace(W_k)) * ((n_samples - n_clusters) / (n_clusters - 1))
    
    return ch_score


def run(params, samples):
    labels_list = []
    
    db = DBSCAN(eps=params['eps'], min_samples=params['min_samples'], output_type='numpy')
    labels_list = db.fit_predict(samples)
    unique_labels = set(labels_list) - {-1}  # Exclude noise
    logging.info(f"Total samples: {len(samples)}, Unique clusters: {len(unique_labels)}")

    # Save the final labels to a file
    np.save(f"{params['task_name']}.npy", labels_list)
    logging.info(f"Final labels saved to {params['task_name']}.npy")

    # Evaluate clustering using Calinski-Harabasz Index and Silhouette Score
    samples_gpu = cp.array(samples)
    labels_gpu = cp.array(labels_list)
    ch_score = calinski_harabasz_score_gpu(samples_gpu, labels_gpu)
    silhouette_avg = silhouette_score(samples, labels_list)
    logging.info(f"Calinski-Harabasz Index: {ch_score}")
    logging.info(f"Silhouette Score: {silhouette_avg}, noise: {Counter(labels_list)[-1]}")

    # Save the evaluation metrics to a file
    with open("evaluation_metrics.txt", "a") as f:
        f.write(f"Task Name: {params['task_name']}\n")
        f.write(f"Calinski-Harabasz Index: {ch_score}\n")
        f.write(f"Silhouette Score: {silhouette_avg}\n")
        f.write(f"noise: {Counter(labels_list)[-1]}\n")
    logging.info("Evaluation metrics saved to evaluation_metrics.txt")


if __name__ == "__main__":
    # with open("./BERTbase-whiten-256(target)_embeddings.npy", "rb") as file:
    #     embeddings = np.load(file)
    #     logging.info(f"Embeddings shape: {embeddings.shape}")
    #     # Plot K-Distance Graph to choose eps
    #     # plot_k_distance(embeddings, k=511)  # You can adjust k based on your min_samples values
        
    #     for min_samples in min_samples_values:
    #         params = {
    #             'task_name': 'BERTbase-whiten-256(target)' + f'_eps{EPS_VALUE}_min_samples{min_samples}',
    #             'eps': EPS_VALUE,
    #             'min_samples': min_samples,
    #         }
    #         logging.info(f"Testing params: {params}")
    #         run(params, embeddings)

    # with open("./BERTlarge-whiten-384(target)_embeddings.npy", "rb") as file:
    #     embeddings = np.load(file)
    #     logging.info(f"Embeddings shape: {embeddings.shape}")
    #     # Plot K-Distance Graph to choose eps
    #     # plot_k_distance(embeddings, k=16)  # You can adjust k based on your min_samples values
        
    #     for min_samples in min_samples_values:
    #         params = {
    #             'task_name': 'BERTlarge-whiten-384(target)' + f'_eps{EPS_VALUE}_min_samples{min_samples}',
    #             'eps': EPS_VALUE,
    #             'min_samples': min_samples,
    #         }
    #         logging.info(f"Testing params: {params}")
    #         run(params, embeddings)

    with open("./ast2vec/last2avg_embeddings.npy", "rb") as file:
        embeddings = np.load(file)
        logging.info(f"Embeddings shape: {embeddings.shape}")
        # Plot K-Distance Graph to choose eps
        # plot_k_distance(embeddings, k=1535)  # You can adjust k based on your min_samples values
        
        for min_samples in min_samples_values:
            params = {
                'task_name': 'last2avg_embeddings' + f'_eps{EPS_VALUE}_min_samples{min_samples}',
                'eps': EPS_VALUE,
                'min_samples': min_samples,
            }
            logging.info(f"Testing params: {params}")
            run(params, embeddings)