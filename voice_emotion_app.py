import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import soundfile as sf
import queue
import matplotlib.pyplot as plt
import os
import time
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from emotion_detection import predict_emotion  # Custom model function
import base64

def autoplay_audio(file_path: str):
    try:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
            b64_audio = base64.b64encode(audio_bytes).decode()

        audio_html = f"""
        <audio autoplay controls>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to load audio file: {e}")

# Load environment variables
load_dotenv()

# Streamlit config
st.set_page_config(page_title="Voice Emotion Music AI", layout="centered")
from streamlit_lottie import st_lottie
import requests

def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_robot = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_zrqthn6o.json")

st_lottie(lottie_robot, height=200, key="robot")
st.markdown("""
    <h1 style='text-align: center; color: #000000; font-size: 2.8em;'>
        🎙️ Real-Time Voice Emotion Music Recommender
    </h1>
""", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        bottom: 10px;
        width: 100%;
        text-align: center;
        color: black;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        Made with ❤️ by Yash Saxena
    </div>
    """,
    unsafe_allow_html=True
)

# Instructions
with st.expander("💡 What should I say to test emotion?"):
    st.markdown("""
    Try speaking naturally for a few seconds with emotional tone. Some examples:

    - 😊 **Happy**: "I'm feeling amazing today! Everything is just perfect!"
    - 😢 **Sad**: "I just don’t feel good… things are really hard right now."
    - 😠 **Angry**: "Why does this always happen to me? I'm so frustrated!"
    - 😐 **Neutral**: "The sky is blue and the grass is green."

    > Speak clearly for **5–10 seconds**, and use tone that matches your emotion.
    """)

# Session state init
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []

# Audio Queue
audio_queue = queue.Queue()

# Audio Processor
class AudioProcessor:
    def __init__(self) -> None:
        self.recorded_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        try:
            # Convert the audio frame to a NumPy array
            audio = frame.to_ndarray()
            
            # Print frame shape in terminal for debug
            if audio is not None and audio.size > 0:
                print(f"🔊 Frame received: {audio.shape}")
            else:
                print("⚠️ Empty or invalid frame received.")
            
            # Push to queue for Streamlit processing
            audio_queue.put(audio)
        except Exception as e:
            print(f"❌ Error while receiving frame: {e}")

        return frame

# Plot waveform
def plot_audio_waveform(audio_chunk):
    if audio_chunk is not None and len(audio_chunk) > 0:
        df = pd.DataFrame(audio_chunk[:1000], columns=["Amplitude"])
        df["Time"] = df.index
        fig = px.line(df, x="Time", y="Amplitude", title="🎧 Live Voice Waveform", height=300)
        fig.update_layout(
            plot_bgcolor='black',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='cyan'),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

# Start WebRTC
webrtc_ctx = webrtc_streamer(
    key="emotion",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=256,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
)

# Buttons
st.markdown("""
    <style>
        .mic-container {
            display: flex;
            justify-content: center;
            margin-top: 30px;
        }

        .pulse-mic {
            width: 60px;
            height: 60px;
            background: radial-gradient(circle, #00d4ff, #0077ff);
            border-radius: 50%;
            position: relative;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(0, 212, 255, 0.7);
            }
            70% {
                box-shadow: 0 0 0 20px rgba(0, 212, 255, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(0, 212, 255, 0);
            }
        }
    </style>

    <div class="mic-container">
        <div class="pulse-mic"></div>
    </div>
""", unsafe_allow_html=True)
start = st.button("🎙️ Start Recording")
stop = st.button("⏹️ Stop & Analyze")

# Manual reset
if st.button("🔁 Reset App"):
    st.session_state.recording = False
    st.session_state.audio_frames = []
    st.rerun()

# Debug states
st.write("Recording:", st.session_state.recording)
st.write("Playing:", webrtc_ctx.state.playing)
st.write("Frames captured:", len(st.session_state.audio_frames))

# Control logic
if start:
    st.session_state.recording = True
    st.info("Recording... Speak into your mic 🎤")

if stop:
    st.session_state.recording = False

# Collect frames
if webrtc_ctx.state.playing and st.session_state.recording:
    with st.spinner("🎤 Listening..."):
        while st.session_state.recording:
            if not audio_queue.empty():
                frame = audio_queue.get()
                if frame is not None and isinstance(frame, np.ndarray):
                    frame_array = frame.flatten()
                    if frame_array.size > 0:
                        st.session_state.audio_frames.append(frame_array)
                        plot_audio_waveform(frame_array[:500])
            time.sleep(0.1)

# Analysis
if not st.session_state.recording and st.session_state.audio_frames:
    st.info("⏳ Analyzing your voice...")
    
    # Save audio
    audio_data = np.concatenate(st.session_state.audio_frames).astype(np.float32)
    sf.write("temp_audio.wav", audio_data, 16000)

    try:
        # Predict emotion
        result = predict_emotion("temp_audio.wav")
        if isinstance(result, dict):
            # If dict like {'Happy': 0.7, ...}, show graph
            predictions = result
            detected_emotion = max(predictions, key=predictions.get)
        else:
            detected_emotion = result
            predictions = {
                detected_emotion.capitalize(): 1.0
            }

        st.success(f"🧠 Detected Emotion: `{detected_emotion.capitalize()}`")

        # Emotion bar chart
        df = pd.DataFrame(list(predictions.items()), columns=["Emotion", "Probability"])
        df["Probability (%)"] = df["Probability"] * 100

        fig = px.bar(
            df,
            x="Emotion",
            y="Probability (%)",
            color="Emotion",
            text_auto=".2f",
            range_y=[0, 100],
            title="Emotion Confidence Score"
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Emotion detection failed: {e}")
        st.stop()

    # Music suggestion
    emotion_queries = {
        "happy": "upbeat pop songs",
        "sad": "emotional acoustic songs",
        "angry": "hard rock",
        "neutral": "lofi chill beats"
    }
    query = emotion_queries.get(detected_emotion.lower(), "lofi chill beats")

    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope="user-read-playback-state,user-modify-playback-state"
        ))

        results = sp.search(q=query, type="track", limit=1)
        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]
            track_name = track["name"]
            track_artist = track["artists"][0]["name"]
            track_url = track["external_urls"]["spotify"]

            st.markdown(f"**🎶 Recommended Track:** {track_name} by {track_artist}")
            st.markdown(f"[🔗 Listen on Spotify]({track_url})")

            # Embed player
            track_id = track_url.split("/")[-1].split("?")[0]
            st.markdown(
                f"""
                <iframe src="https://open.spotify.com/embed/track/{track_id}"
                    width="100%" height="80" frameborder="0"
                    allowtransparency="true" allow="encrypted-media">
                </iframe>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("No track found for this emotion.")
    except Exception as e:
        st.warning(f"🎵 Spotify failed: {e}")

    # Reset
    st.session_state.audio_frames = []