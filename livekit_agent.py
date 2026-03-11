import asyncio
import time
import numpy as np
import soundfile as sf
import threading

from dotenv import load_dotenv
load_dotenv()

from livekit.agents import WorkerOptions, cli
from livekit import rtc

from faster_whisper import WhisperModel

from sentiment_pipeline import analyze_audio
from text_sentiment import analyze_text
from stress_trigger import check_stress
from response_engine import generate_response
from summary_tool import create_summary, create_handoff_summary
from handoff import transfer_to_human
from text_to_speech import speak


WANT_HUMAN_PHRASES = [
    "talk to human", "speak to human", "talk to a human", "speak to a human",
    "want to talk to human", "need to talk to human", "i need a human",
    "want a human", "need a human", "human agent", "real person", "real agent",
    "not ai", "not the ai", "don't want ai", "connect me to human",
    "transfer to human", "transfer me", "let me talk to someone",
    "human please", "agent please", "customer service", "live agent",
]


def wants_human(text):
    lower = text.strip().lower()
    return any(p in lower for p in WANT_HUMAN_PHRASES)


model = WhisperModel("base", compute_type="int8")

conversation_history = []

is_speaking = False
SPEECH_COOLDOWN_SEC = 1.5
last_speech_end_time = 0.0


async def process_audio(audio_frames):

    audio = np.concatenate(audio_frames)
    file = "temp_audio.wav"

    sf.write(file, audio, 48000)

    segments, _ = model.transcribe(
        file,
        beam_size=5,
        vad_filter=True,
        language="en"
    )

    text = ""

    for seg in segments:
        text += seg.text

    return text.strip(), file


async def handle_audio(track):

    global is_speaking, last_speech_end_time

    if track.kind != rtc.TrackKind.KIND_AUDIO:
        return

    print("🎤 Listening...")

    audio_stream = rtc.AudioStream(track)

    frames = []
    speech_started = False
    silence_counter = 0

    async for frame in audio_stream:

        if is_speaking or (time.monotonic() - last_speech_end_time) < SPEECH_COOLDOWN_SEC:
            frames.clear()
            speech_started = False
            silence_counter = 0
            continue

        try:
            raw = frame.frame.data
        except AttributeError:
            raw = getattr(frame, "data", None)

        if raw is None:
            continue

        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        volume = np.abs(samples).mean()

        # Lower threshold for better speech detection
        if volume > 0.01:

            speech_started = True
            silence_counter = 0
            frames.append(samples)

        elif speech_started:

            silence_counter += 1

            if silence_counter < 20:
                frames.append(samples)
                continue

            if len(frames) < 40:
                frames.clear()
                speech_started = False
                silence_counter = 0
                continue

            try:

                text, audio_file = await process_audio(frames)

                frames.clear()
                speech_started = False
                silence_counter = 0

                if len(text) < 3:
                    continue

                print("\n User said:", text)

                conversation_history.append("User: " + text)

                if wants_human(text):

                    summary = create_handoff_summary(conversation_history)

                    msg = "I'll connect you with a human agent now."

                    speak(msg)

                    transfer_to_human(summary)
                    continue

                # -------------------------
                # AUDIO SENTIMENT
                # -------------------------

                try:
                    print("Running audio analysis...")
                    audio_score = analyze_audio(audio_file)
                except Exception as e:
                    print("Audio analysis failed:", e)
                    audio_score = 0.5

                # -------------------------
                # TEXT SENTIMENT
                # -------------------------

                try:
                    print("Running text sentiment...")
                    text_score = analyze_text(text)
                except Exception as e:
                    print("Text sentiment failed:", e)
                    text_score = "neutral"

                # -------------------------
                # STRESS LEVEL
                # -------------------------

                try:
                    stress_level = check_stress(audio_score, text_score)
                except Exception as e:
                    print("Stress check failed:", e)
                    stress_level = "NORMAL"

                print(" Stress level:", stress_level)

                # -------------------------
                # RESPONSE GENERATION
                # -------------------------

                try:

                    response = generate_response(
                        text,
                        stress_level,
                        conversation_history
                    )

                except Exception as e:

                    print("LLM error:", e)

                    response = "I'm here to help. Could you please explain your issue again?"

                print(" Agent:", response)

                conversation_history.append("Agent: " + response)

                # -------------------------
                # SPEAK RESPONSE
                # -------------------------

                try:

                    is_speaking = True

                    t = threading.Thread(
                        target=speak,
                        args=(response,),
                        daemon=True
                    )

                    t.start()

                    await asyncio.to_thread(t.join)

                except Exception as e:

                    print("TTS error:", e)

                finally:

                    is_speaking = False
                    last_speech_end_time = time.monotonic()

                # -------------------------
                # ESCALATE IF HIGH STRESS
                # -------------------------

                if stress_level == "HIGH":

                    summary = create_summary(conversation_history)

                    transfer_to_human(summary)

            except Exception as e:

                print("Processing error:", e)


async def entrypoint(ctx):

    print(" Agent starting...")

    await ctx.connect()

    print(f" Connected to room: {ctx.room.name}")

    def on_track(track, publication, participant):

        try:
            pname = getattr(participant, "identity", None) or getattr(participant, "name", None) or "unknown"
        except Exception:
            pname = "unknown"

        print(f"🎙 Audio track subscribed from: {pname}")

        asyncio.create_task(handle_audio(track))

    ctx.room.on("track_subscribed", on_track)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )
