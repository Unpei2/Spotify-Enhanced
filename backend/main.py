import spotipy
import random
import re
import os
import subprocess
import numpy as np
import shutil
import processing_clips as pc

from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from spotdl import Spotdl
from pydub import AudioSegment
from pathlib import Path



load_dotenv()

SEPARATOR = "\n----------\n"


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




def download_songs(playlist):
    playlistUri = playlist['external_urls']['spotify']
    name = pc.name_converter(playlist['name'])
    
    downloadLocation = pc.BACKEND_DIR / "music_downloads"

    subprocess.run(["spotdl", "download", playlistUri, "--output", f"{name}_downloads", "--audio", "youtube", "--save-errors", f"{name}_failed_downloads.txt"]
                   , cwd=downloadLocation)

    failed = downloadLocation / f"{name}_failed_downloads.txt"
    if failed.exists():
        with open(f"{downloadLocation}/{name}_failed_downloads.txt", "r") as file:
            items = file.read().splitlines()

        print(items)

def main():
    
    scope = "user-library-read user-read-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-modify-playback-state playlist-modify-public playlist-modify-private"
    
    try: 
        os.mkdir(pc.BACKEND_DIR/"music_downloads")
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
    

        
    # download_songs(playlists[0])
    # pc.get_clips(playlists[0])
    pc.get_embeddings(playlists[0])
    print("abracadabra")

if __name__ == "__main__":
    
    main()

