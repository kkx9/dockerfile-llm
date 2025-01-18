import cupy as cp
import logging
import numpy as np
from cuml.cluster import KMeans
from cuml.metrics.cluster import silhouette_score


logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.DEBUG)


def calinski_harabasz_score_gpu(X, labels):
    n_samples, n_features = X.shape
    n_clusters = len(cp.unique(labels))

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
    
    kmeans = KMeans(n_clusters=params['n_clusters'], random_state=42)
    kmeans.fit_predict(samples)
    labels_list = kmeans.labels_
    unique_labels = set(labels_list)
    logging.info(f"Total samples: {len(samples)}, Unique clusters: {len(unique_labels)}")

    # np.save(f"{params['task_name']}.npy", labels_list)
    # logging.info(f"Final labels saved to {params['task_name']}.npy")

    samples_gpu = cp.array(samples)
    labels_gpu = cp.array(labels_list)
    ch_score = calinski_harabasz_score_gpu(samples_gpu, labels_gpu)
    silhouette_avg = silhouette_score(samples, labels_list)
    logging.info(f"Calinski-Harabasz Index: {ch_score}")
    logging.info(f"Silhouette Score: {silhouette_avg}")

    with open("kmeans_evaluation_metrics_fla.txt", "a") as f:
        f.write(f"Task Name: {params['task_name']}\n")
        f.write(f"Calinski-Harabasz Index: {ch_score}\n")
        f.write(f"Silhouette Score: {silhouette_avg}\n")
    logging.info("Evaluation metrics saved to kmeans_evaluation_metrics_fla.txt")


if __name__ == "__main__":
    max_cluster = 20
    with open("./ast2vec/first_last_avg_embeddings.npy", "rb") as file:
        embeddings = np.load(file)
        logging.info(f"Embeddings shape: {embeddings.shape}")
        # Plot K-Distance Graph to choose eps
        # plot_k_distance(embeddings, k=511)  # You can adjust k based on your min_samples values
        
        for k in range(2, max_cluster + 1):
            params = {
                'task_name': 'first_last_avg_embeddings' + f'_k{k}',
                'n_clusters': k,
            }
            logging.info(f"Testing params: {params}")
            run(params, embeddings)
