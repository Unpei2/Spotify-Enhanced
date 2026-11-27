import random

def euclidean_distance(p1, p2):
    pass

def fischer_yates_shuffle(songs):
    
    for i in range((len(songs)) - 1, 0  , -1):
        j = random.randint(0, i)
        temp = songs[i]
        songs[i] = songs[j]
        songs[j] = temp