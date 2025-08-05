from dotenv import load_dotenv
import os

load_dotenv()  # loads .env

print("Client ID:", os.getenv("SPOTIFY_CLIENT_ID"))
print("Client Secret:", os.getenv("SPOTIFY_CLIENT_SECRET"))
print("Redirect URI:", os.getenv("REDIRECT_URI"))