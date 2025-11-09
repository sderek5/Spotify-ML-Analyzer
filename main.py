import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time

# ---------------- Spotify Auth ----------------
def init_spotify():
    os.environ['SPOTIPY_CLIENT_ID'] = '18b00fe3ef5e436bb0570c04b7dcb2d8'
    os.environ['SPOTIPY_CLIENT_SECRET'] = '05734e0c68c247939099fb7b1f410124'
    os.environ['SPOTIPY_REDIRECT_URI'] = 'http://127.0.0.1:8888/callback'
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="playlist-read-private",
        redirect_uri=os.environ['SPOTIPY_REDIRECT_URI']
    ))

# ---------------- Fetch All Playlist Tracks ----------------
def fetch_playlist_tracks(sp, playlist_id):
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100, offset=0)
    
    while results:
        for item in results['items']:
            track = item.get('track')
            if track:
                tracks.append({
                    "spotify_id": track['id'],
                    "name": track['name'],
                    "artists": [artist['name'] for artist in track['artists']],
                    "artist_ids": [artist['id'] for artist in track['artists']]
                })
        
        # Check if there's a next page
        if results['next']:
            results = sp.next(results)
        else:
            break

    print(f"Found {len(tracks)} tracks in the playlist.")
    return tracks

# ---------------- Fetch ReccoBeats + Spotify Data ----------------
def fetch_track_data(sp, tracks):
    all_data = []
    headers = {"Accept": "application/json"}

    for idx, track in enumerate(tracks, 1):
        spotify_id = track['spotify_id']
        track_name = track['name']
        artist_names = track['artists']

        try:
            # --- ReccoBeats lookup ---
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

            # --- Get audio features ---
            features_url = f"https://api.reccobeats.com/v1/track/{recco_uuid}/audio-features"
            features_response = requests.get(features_url, headers=headers)
            if features_response.status_code != 200:
                print(f"[{idx}] Failed to fetch audio features for '{track_name}': {features_response.status_code}")
                continue

            features_data = features_response.json()

            # --- Spotify metadata ---
            spotify_metadata = sp.track(spotify_id)

            combined = {
                "track_name": track_name,
                "artist_names": ", ".join(artist_names),
                "spotify_id": spotify_id,
                "recco_uuid": recco_uuid,
                "duration_ms": spotify_metadata.get("duration_ms"),
                "popularity": spotify_metadata.get("popularity"),
                "album_name": spotify_metadata['album']['name'],
                "release_date": spotify_metadata['album']['release_date'],
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
            print(f"[{idx}] ✅ '{track_name}' fetched successfully.")
            time.sleep(0.1)

        except Exception as e:
            print(f"[{idx}] ❌ Error processing '{track_name}': {e}")

    return all_data

# ---------------- Main Execution ----------------
if __name__ == "__main__":
    sp = init_spotify()
    playlist_id = "5SxG5yIfVryB1UClEPNc7n"

    tracks = fetch_playlist_tracks(sp, playlist_id)
    all_data = fetch_track_data(sp, tracks)

    df = pd.DataFrame(all_data)
    df.to_csv("playlist_audio_features.csv", index=False)
    print("✅ All data saved to 'playlist_audio_features.csv'")