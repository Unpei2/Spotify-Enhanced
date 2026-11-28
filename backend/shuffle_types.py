import random
import numpy as np
import os

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

def fischer_yates_shuffle(songs):
    
    for i in range((len(songs)) - 1, 0  , -1):
        j = random.randint(0, i)
        temp = songs[i]
        songs[i] = songs[j]
        songs[j] = temp


def knn_search_one_vector(prospect, k):
    embeddingsPath = BACKEND_DIR / "embeddings"

    embeddings = os.listdir(embeddingsPath)
    vectors = np.stack([np.load(vector) for vector in embeddings])   # (total_clips, 1024)


    distance = np.linalg.norm()



def knn_search_min_vectors(prospect, k):
    # want to implement 3 vectors for one song later (maybe more accurate)
    pass

