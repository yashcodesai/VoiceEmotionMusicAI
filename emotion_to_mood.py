def emotion_to_mood_query(emotion):
    mapping = {
        "happy": "upbeat pop songs",
        "sad": "sad instrumental",
        "angry": "calm classical music",
        "neutral": "focus playlist",
        "fear": "relaxing ambient",
        "surprise": "exciting edm"
    }
    return mapping.get(emotion.lower(), "chill music")