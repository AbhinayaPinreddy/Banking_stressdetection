def check_stress(audio_score, text_score):
    """
    Both scores 0-1. HIGH = worried/urgent/angry or raised voice (even somewhat) → calm them. NORMAL = calm request.
    """
    # Raised voice / somewhat shouting → calm them politely, even if words are neutral
    if audio_score >= 0.42:
        return "HIGH"
    final_score = (audio_score * 0.6) + (text_score * 0.4)
    if final_score > 0.42:
        return "HIGH"
    return "NORMAL"