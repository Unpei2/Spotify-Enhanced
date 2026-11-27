import numpy as np
import os
import shutil
import sys
import torch


from pydub import AudioSegment
from pathlib import Path
from musicfm.model.musicfm_25hz import MusicFM25Hz

BACKEND_DIR = Path(__file__).resolve().parent

def name_converter(name):
    temp = name.split(" ")
    return "_".join(temp)

def get_clips(playlist):
    name = name_converter(playlist['name'])
    path  = BACKEND_DIR / f"music_downloads/{name}_downloads"
    clipsPath = BACKEND_DIR / f"clips/{name}_clips"
    songs = os.listdir(path)
    
    all_clips = {}
    for item in songs:
        print(item)
        
        
        audio_clips = []
        song = AudioSegment.from_mp3(f"{path}/{item}").set_channels(1).set_frame_rate(24000)
    
        fullSections = song.duration_seconds // 30

        for i in range(1, int(fullSections) + 1):
            # time is in milliseconds
            start = (i-1) * 30000
            end = i * 30000
            audio_clips.append(song[start : end])

        # for the end, take the last 30 seconds instead of padding with silence to get more accurate representation of song
        # if the clip has a remainder of one second at the end, it would have 29 secs of silence
        if song.duration_seconds % 30 > 0:
            end = song[-30000:]
            audio_clips.append(end)

        # convert to numpy float32 array
        arrs = []
        for clip in audio_clips:
            samples = clip.get_array_of_samples()
            arr = np.array(samples, dtype=np.float32)
            arr /= np.iinfo(samples.typecode).max
            arrs.append(arr)

        all_clips[item] = arrs

    # make clips folder
    clipsPath.mkdir(parents=True, exist_ok=True)
    for song, clips in all_clips.items():
        np.save(clipsPath / Path(song).stem, clips)

    # remove music donwloads folder of mp3s (dont need after making clips)
    shutil.rmtree(path)


def get_embeddings(playlist):
    name = name_converter(playlist['name'])

    musicfmPath = BACKEND_DIR / "musicfm"
    clipsPath = BACKEND_DIR / f"clips/{name}_clips"
    embeddingsPath = BACKEND_DIR / f"embeddings/{name}_embeddings"

    songs = os.listdir(clipsPath)

    # Make embeddings folder
    embeddingsPath.mkdir(parents=True, exist_ok=True)

    # use gpu if available
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # create the model, using the msd dataset
    musicfm = MusicFM25Hz(
                    is_flash=False,
                    stat_path=os.path.join(musicfmPath, "data", "msd_stats.json"),
                    model_path=os.path.join(musicfmPath, "data", "pretrained_msd.pt"),
                ).to(device).eval()

    for song in songs:
        if (embeddingsPath / song).exists():
            print(song, "embedding already created")
            continue

        print(song)
        allClips = np.load( clipsPath / song)


        # for testing if input is correct
        # x = torch.from_numpy(allClips[:1])          # first clip, keeps batch axis

        # print(x.shape)                           # torch.Size([1, 720000])
        # print(x.dtype)                           # torch.float32
        # print(x.min().item(), x.max().item())    # both within -1..1
        # print(torch.isnan(x).any().item())       # False
        # print(x.abs().max().item())              # not ~0 (a silent clip means a bug)
        
        toSave = []

        with torch.no_grad():
            for clip in allClips:
                x = torch.from_numpy(clip)[None].to(device)
                emb = musicfm.get_latent(x, layer_ix=7)
                toSave.append(emb.mean(dim=1).squeeze(0).cpu())
                # print(emb.shape)
                


        np.save(embeddingsPath / Path(song).stem, torch.stack(toSave).numpy())

    # remove clips folder of numpys (dont need after making embeddings)
    shutil.rmtree(clipsPath)
    