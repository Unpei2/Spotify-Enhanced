import spotipy
import random
import re
import os
import subprocess
import numpy as np
import shutil

from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from spotdl import Spotdl
from pydub import AudioSegment
from pathlib import Path


load_dotenv()

SEPARATOR = "\n----------\n"
BACKEND_DIR = Path(__file__).resolve().parent

def add_songs_to_playlist(sp, songList, playlist):

    for i in range(0, len(songList), 100):
        sp.playlist_add_items(playlist["id"], 
            [song['uri'] for song in songList[i:i+100]]
        )
    
def create_playlist(sp):

    playlists = get_playlists(sp)

    matches = re.findall("Enhanced Playlist", " ".join([playlist['name'] for playlist in playlists]))
    count = len(matches)
    sp.current_user_playlist_create(f"Enhanced Playlist {count + 1}", False, False, "Playlist made with spotify Enhanced.")

def add_songs_to_queue(sp, songList):

    try:
        for song in songList:
            sp.add_to_queue(song['uri'])
    except Exception:
        print("Spotify player must be open.")

def fischer_yates_shuffle(songs):
    
    for i in range((len(songs)) - 1, 0  , -1):
        j = random.randint(0, i)
        temp = songs[i]
        songs[i] = songs[j]
        songs[j] = temp

def print_song_information(song):
    
    songName = song['name']
    songArtist = song['artists'][0]['name']
    songAlbum = song['album']['name']
    print(f'{songName} by {songArtist} --- Album: {songAlbum}')
    print(SEPARATOR)

def current_song(sp):

    current = sp.current_playback()

    if current == None:
        print("No song is playing at the moment.")
        print(SEPARATOR)
        return

    track = current['item']

    print("Currently playing:")
    print_song_information(track)
    return
    
def get_playlists(sp):

    playlists = []
    limit = 50
    offset = 0
    while True:
        playlist = sp.current_user_playlists(limit, offset)
        for item in playlist['items']:
            playlists.append(item)

        if len(playlist['items']) < limit:
                    break

        offset = offset + limit

    return playlists

def get_songs(sp, playlist):
    
    songs = []
    limit = 50
    offset = 0

    while True:
        result = sp.playlist_items(playlist['id'], limit=limit, offset=offset)
        
        for song in result['items']:
            songs.append(song['item'])

        if len(result['items']) < limit:
            break

        offset = offset + limit

    count = 0

    for song in songs:
        count += 1
        print(count, song['name'], "from",song['album']['name'])

    return songs
        
def get_uris(songs):
    song_uris = []

    for song in songs:
        song_uris.append(song['uri'])

    return song_uris

def name_converter(name):
    temp = name.split(" ")
    return "_".join(temp)


def download_songs(playlist):
    playlistUri = playlist['external_urls']['spotify']
    name = name_converter(playlist['name'])
    
    downloadLocation = BACKEND_DIR / "music_downloads"

    subprocess.run(["spotdl", "download", playlistUri, "--output", f"{name}_downloads", "--audio", "youtube", "--save-errors", f"{name}_failed_downloads.txt"]
                   , cwd=downloadLocation)

    failed = downloadLocation / f"{name}_failed_downloads.txt"
    if failed.exists():
        with open(f"{downloadLocation}/{name}_failed_downloads.txt", "r") as file:
            items = file.read().splitlines()

        print(items)

def pad_end(x, n):
    pass

def get_clips(playlist):
    name = name_converter(playlist['name'])
    path  = BACKEND_DIR / f"music_downloads/{name}_downloads"
    embeddingsPath = BACKEND_DIR / f"embeddings/{name}_embeddings"
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
    # make embeddings folder
    embeddingsPath.mkdir(parents=True, exist_ok=True)
    for song, embeddings in all_clips.items():
        np.save(embeddingsPath / Path(song).stem, embeddings)

    # remove music donwloads folder of mp3s (dont need after making embeddings)
    shutil.rmtree(path)
        

def main():
    
    scope = "user-library-read user-read-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-modify-playback-state playlist-modify-public playlist-modify-private"
    
    try: 
        os.mkdir(BACKEND_DIR/"music_downloads")
        print("Music Downloads folder created")
    except FileExistsError:
        print("music_downloads already made.")
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    print(SEPARATOR)
    
    current_song(sp)
    playlists = get_playlists(sp)

    for item in playlists:
        print(item['name'])

    print(SEPARATOR)
    

    songs = get_songs(sp, playlists[0])

    print(SEPARATOR)

    # add_songs_to_queue(sp, songs)

    print(SEPARATOR)

    # create_playlist(sp)

    # playlists = get_playlists(sp)
    # add_songs_to_playlist(sp, songs, playlists[0])

    # song_uris = get_uris(songs)
    # print(song_uris)

    print(playlists[0].keys())
    

        
    download_songs(playlists[0])
    get_clips(playlists[0])
    print("abracadabra")

if __name__ == "__main__":
    
    main()

