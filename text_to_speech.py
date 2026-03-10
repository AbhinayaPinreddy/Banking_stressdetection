import pyttsx3

try:
    import winsound
except ImportError:  # non‑Windows or unavailable
    winsound = None


def speak(text: str) -> None:
    """
    Speak text using pyttsx3 (Windows SAPI5).
    Each call creates a new engine to avoid freeze issues.
    """
    if not text or text.strip() == "":
        return

    try:
        print("🔊 Speaking:", text)

        # Ensure we use the Windows SAPI driver explicitly.
        engine = pyttsx3.init(driverName="sapi5")

        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)

        # Prefer a female, softer voice when available.
        try:
            voices = engine.getProperty("voices")
            chosen = None
            for v in voices:
                name = (getattr(v, "name", "") or "").lower()
                # Common Windows female voices include Zira, Heera, etc.
                if any(tag in name for tag in ["zira", "heera", "female", "woman", "girl"]):
                    chosen = v
                    break
            # Fallback: if we didn't detect by name but voices exist, pick the last one
            # (often a different timbre than the default).
            if chosen is None and voices:
                chosen = voices[-1]
            if chosen is not None:
                engine.setProperty("voice", chosen.id)
        except Exception:
            # If voice selection fails, just keep the default.
            pass

        # Optional: short beep so we can confirm any sound is coming out at all.
        if winsound is not None:
            try:
                winsound.Beep(880, 120)
            except Exception:
                # Ignore beep issues; focus on speech.
                pass

        engine.say(text)
        engine.runAndWait()
        engine.stop()

    except Exception as e:
        print("TTS Error:", e)