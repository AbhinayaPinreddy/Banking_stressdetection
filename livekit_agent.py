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

# Phrases that mean the customer wants to talk to a human (not AI)
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

from text_to_speech import speak


model = WhisperModel("base",compute_type="int8")

conversation_history = []

is_speaking = False
# Ignore mic for this many seconds after agent finishes speaking (avoids echo/noise)
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

        # -----------------------------
        # FIX 1: Ignore mic while agent speaking
        # -----------------------------
        if is_speaking:
            frames.clear()
            speech_started = False
            silence_counter = 0
            continue

        # -----------------------------
        # Cooldown: ignore mic briefly after agent spoke (avoids echo / false triggers)
        # -----------------------------
        if (time.monotonic() - last_speech_end_time) < SPEECH_COOLDOWN_SEC:
            frames.clear()
            speech_started = False
            silence_counter = 0
            continue

        samples = np.frombuffer(
            frame.frame.data,
            dtype=np.int16
        ).astype(np.float32) / 32768.0

        volume = np.abs(samples).mean()

        # -----------------------------
        # Speech detection (0.04 = less sensitive to background noise)
        # -----------------------------
        if volume > 0.04:

            speech_started = True
            silence_counter = 0

            frames.append(samples)

        elif speech_started:

            silence_counter += 1

            # Need more silence frames before considering speech ended (reduces false triggers)
            if silence_counter < 22:
                frames.append(samples)
                continue

            # -----------------------------
            # Speech finished (ignore very short bursts)
            # -----------------------------
            if len(frames) < 100:
                frames.clear()
                speech_started = False
                silence_counter = 0
                continue

            try:

                text, audio_file = await process_audio(frames)

                # -----------------------------
                # FIX 2: Clear everything
                # -----------------------------
                frames.clear()
                speech_started = False
                silence_counter = 0

                if len(text) < 5:
                    continue

                print("\n👤 User said:", text)

                conversation_history.append("User: " + text)

                # -----------------------------
                # Transfer to human if requested
                # -----------------------------
                if wants_human(text):
                    summary = create_handoff_summary(conversation_history)
                    is_speaking = True
                    hold_msg = "I'll connect you with a human agent now. Please hold."
                    t = threading.Thread(target=speak, args=(hold_msg,), daemon=True)
                    t.start()
                    await asyncio.to_thread(t.join)
                    is_speaking = False
                    last_speech_end_time = time.monotonic()
                    transfer_to_human(summary)
                    continue

                audio_score = analyze_audio(audio_file)
                text_score = analyze_text(text)

                stress_level = check_stress(audio_score, text_score)

                print("📊 Stress level:", stress_level)

                response = generate_response(
                    text,
                    stress_level,
                    conversation_history
                )

                print("🤖 Agent:", response)

                conversation_history.append("Agent: " + response)

                # -----------------------------
                # Speak response
                # -----------------------------
                is_speaking = True

                t = threading.Thread(
                    target=speak,
                    args=(response,),
                    daemon=True
                )
                t.start()

                # -----------------------------
                # FIX 3: wait until speaking finishes
                # -----------------------------
                await asyncio.to_thread(t.join)

                is_speaking = False
                last_speech_end_time = time.monotonic()

                # -----------------------------
                # Escalation
                # -----------------------------
                if stress_level == "HIGH":

                    summary = create_summary(conversation_history)
                    transfer_to_human(summary)

            except Exception as e:

                print("Processing error:", e)


async def entrypoint(ctx):

    print("🚀 Agent starting...")

    await ctx.connect()

    print(f"✅ Connected to room: {ctx.room.name}")

    def on_track(track, publication, participant):

        print("🎙 Microphone connected")

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