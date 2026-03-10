from textblob import TextBlob

# Phrases that show worry, urgency, or tension — customer may need reassurance/calming
URGENCY_PHRASES = [
    "please help", "help me", "i need help", "need help", "lost my card", "lost my",
    "i lost", "stolen", "missing", "can't find", "cant find", "urgent", "emergency",
    "not working", "doesn't work", "doesnt work", "wrong", "problem", "issue",
    "scared", "worried", "anxious", "panic", "fraud", "unauthorized",
]

def analyze_text(text):
    """
    High score if: (1) negative/angry sentiment, OR (2) worried/urgent phrasing.
    Normal "check my balance" -> 0. "Please help I lost my card" -> elevated (calm them).
    """
    lower = text.strip().lower()
    # Worry/urgency: they need a calming, reassuring response
    urgency = 0.7 if any(p in lower for p in URGENCY_PHRASES) else 0.0
    # Anger/negative sentiment
    sentiment = TextBlob(text).sentiment.polarity  # -1 to +1
    sentiment_stress = max(0.0, -sentiment)
    # Use whichever is higher so either urgent OR angry triggers calming tone
    return max(urgency, sentiment_stress)