import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import pandas as pd
import time

# --- 1. Spotify Authentication ---
os.environ['SPOTIPY_CLIENT_ID'] = '18b00fe3ef5e436bb0570c04b7dcb2d8'
os.environ['SPOTIPY_CLIENT_SECRET'] = '05734e0c68c247939099fb7b1f410124'
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://127.0.0.1:8888/callback'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="playlist-read-private",
    redirect_uri=os.environ['SPOTIPY_REDIRECT_URI']
))

# --- 2. Get Playlist Tracks ---
playlist_id = "5SxG5yIfVryB1UClEPNc7n"
results = sp.playlist_items(playlist_id, limit=100)
tracks = [
    {
        "spotify_id": item['track']['id'],
        "name": item['track']['name'],
        "artist": item['track']['artists'][0]['name']
    }
    for item in results['items'] if item['track'] is not None
]

print(f"Found {len(tracks)} tracks in the playlist.")

# --- 3. Loop through all tracks and fetch data ---
all_data = []
headers = {"Accept": "application/json"}

for idx, track in enumerate(tracks, 1):
    spotify_id = track['spotify_id']
    track_name = track['name']
    artist_name = track['artist']
    
    # --- Get Recco UUID ---
    try:
        multi_track_url = f"https://api.reccobeats.com/v1/track?ids={spotify_id}"
        response = requests.get(multi_track_url, headers=headers)
        if response.status_code != 200:
            print(f"[{idx}] Failed ReccoBeats lookup for '{track_name}': {response.status_code}")
            continue
        
        data = response.json()
        if "content" not in data or not data["content"]:
            print(f"[{idx}] No ReccoBeats entry for '{track_name}'")
            continue
        
        recco_uuid = data["content"][0]["id"]
        
        # --- Get detailed audio features ---
        features_url = f"https://api.reccobeats.com/v1/track/{recco_uuid}/audio-features"
        features_response = requests.get(features_url, headers=headers)
        if features_response.status_code != 200:
            print(f"[{idx}] Failed to fetch audio features for '{track_name}': {features_response.status_code}")
            continue
        
        features_data = features_response.json()
        
        # --- Get Spotify metadata ---
        spotify_metadata = sp.track(spotify_id)
        
        # --- Combine everything ---
        combined = {
            "track_name": track_name,
            "artist_name": artist_name,
            "spotify_id": spotify_id,
            "recco_uuid": recco_uuid,
            "duration_ms": spotify_metadata.get("duration_ms"),
            "popularity": spotify_metadata.get("popularity"),
            "album_name": spotify_metadata['album']['name'],
            "release_date": spotify_metadata['album']['release_date'],
            # ReccoBeats audio features
            "acousticness": features_data.get("acousticness"),
            "danceability": features_data.get("danceability"),
            "energy": features_data.get("energy"),
            "instrumentalness": features_data.get("instrumentalness"),
            "key": features_data.get("key"),
            "liveness": features_data.get("liveness"),
            "loudness": features_data.get("loudness"),
            "mode": features_data.get("mode"),
            "speechiness": features_data.get("speechiness"),
            "tempo": features_data.get("tempo"),
            "valence": features_data.get("valence"),
            "spotify_href": spotify_metadata.get("external_urls", {}).get("spotify"),
            "album_href": spotify_metadata['album']['external_urls']['spotify']
        }
        all_data.append(combined)
        print(f"[{idx}] Fetched '{track_name}' successfully.")
        
        # --- Optional: small delay to avoid rate limits ---
        time.sleep(0.2)
    
    except Exception as e:
        print(f"[{idx}] Error processing '{track_name}': {e}")

# --- 4. Save to CSV ---
df = pd.DataFrame(all_data)
df.to_csv("playlist_audio_features.csv", index=False)
print("All data saved to 'playlist_audio_features.csv'")