def create_summary(history):
    last_messages = history[-3:]
    return " ".join(last_messages)


def create_handoff_summary(history):
    """Full conversation summary for human agent when call is transferred."""
    if not history:
        return "No conversation yet."
    # Include full conversation (or last 20 messages if very long)
    messages = history[-20:] if len(history) > 20 else history
    return "\n".join(messages)