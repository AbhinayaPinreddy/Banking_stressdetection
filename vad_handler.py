def user_interrupts(user_speaking):

    if user_speaking:
        return "STOP_AI"

    return "CONTINUE"