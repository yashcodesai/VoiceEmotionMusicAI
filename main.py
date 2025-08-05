import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser

# Load your Spotify credentials
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    scope="user-read-playback-state,user-modify-playback-state"
))

# Example detected emotion to query
emotion = "happy"
query = "upbeat pop songs" if emotion == "happy" else emotion

# Search for a track
results = sp.search(q=query, limit=1, type='track')

if results['tracks']['items']:
    track = results['tracks']['items'][0]
    track_name = track['name']
    artist_name = track['artists'][0]['name']
    track_url = track['external_urls']['spotify']

    print(f"🎵 Track: {track_name} by {artist_name}")
    print(f"🔗 Opening in browser: {track_url}")
    webbrowser.open(track_url)
else:
    print("No tracks found.")