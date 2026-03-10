import pyttsx3

def speak(text):
    """
    Speak text using pyttsx3
    Each call creates a new engine to avoid freeze issues
    """

    if not text or text.strip() == "":
        return

    try:
        print("🔊 Speaking:", text)

        engine = pyttsx3.init()

        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)

        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)

        engine.say(text)
        engine.runAndWait()

        engine.stop()

    except Exception as e:
        print("TTS Error:", e)