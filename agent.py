print("Starting Banking Voice Agent...")

from speech_to_text import transcribe
from sentiment_pipeline import analyze_audio
from text_sentiment import analyze_text
from stress_trigger import check_stress
from response_engine import generate_response

print("Modules imported successfully")

# Test run
audio_file = r"C:\Users\hp\Downloads\file_example_WAV_1MG.wav"

print("Testing pipeline...")

try:
    text = transcribe(audio_file)
    print("Speech to text:", text)

    audio_stress = analyze_audio(audio_file)
    print("Audio stress score:", audio_stress)

    text_stress = analyze_text(text)
    print("Text stress score:", text_stress)

    decision = check_stress(audio_stress, text_stress)
    print("Stress level decision:", decision)

    history = [f"User: {text}"]
    response = generate_response(text, decision, history)
    print("AI Response:", response)

except Exception as e:
    print("Error:", e)