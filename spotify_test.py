import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load credentials from .env
load_dotenv()

# Create Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state"
))

# Search for happy songs
results = sp.search(q='happy songs', type='track', limit=5)

# Display track names
for idx, track in enumerate(results['tracks']['items']):
    print(f"{idx+1}: {track['name']} by {track['artists'][0]['name']}")