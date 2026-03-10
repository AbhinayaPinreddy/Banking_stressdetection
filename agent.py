print("Starting Banking Voice Agent...")

from speech_to_text import transcribe
from sentiment_pipeline import analyze_audio
from stress_trigger import check_stress
from response_engine import generate_response

print("Modules imported successfully")

# Test run
audio_file = r"C:\Users\hp\Downloads\file_example_WAV_1MG.wav"

print("Testing pipeline...")

try:
    text = transcribe(audio_file)
    print("Speech to text:", text)

    stress = analyze_audio(audio_file)
    print("Stress level:", stress)

    decision = check_stress(stress)
    print("Decision:", decision)

    response = generate_response(text)
    print("AI Response:", response)

except Exception as e:
    print("Error:", e)