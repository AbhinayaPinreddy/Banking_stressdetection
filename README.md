# Stress Detection Banking Voice Agent

A voice agent that joins LiveKit meetings, transcribes speech, detects stress from audio and text sentiment, and responds with supportive replies. It can also hand off to a human when requested.

---

## Prerequisites

- **Python 3.10+**
- **Docker** (for running the LiveKit server)
- **Microphone** (for joining the meeting)

---

## Setup & Run

### 1. Install requirements

From the project folder:

```bash
pip install -r requirements.txt
```

*(Optional)* Use a virtual environment:

```bash
python -m venv stressenv
stressenv\Scripts\activate   # Windows
# source stressenv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

---

### 2. Create API key and `.env` file

1. **Create a Groq API key**  
   - Go to [console.groq.com](https://console.groq.com)  
   - Sign up or log in  
   - Create an API key and copy it  

2. **Create a `.env` file** in the project root folder with these variable names:

   ```env
   LIVEKIT_URL=ws://localhost:7880
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   GROQ_API_KEY=your_groq_api_key
   ```

   Replace the placeholders with your actual values:
   - **LIVEKIT_URL** – WebSocket URL for your LiveKit server (use `ws://localhost:7880` for local Docker)
   - **LIVEKIT_API_KEY** – LiveKit API key (e.g. `devkey` for local dev)
   - **LIVEKIT_API_SECRET** – LiveKit API secret (must match the secret used in the Docker `LIVEKIT_KEYS`)
   - **GROQ_API_KEY** – Your Groq API key from [console.groq.com](https://console.groq.com)

   > **Important:** Do not commit `.env` to git. Add `.env` to your `.gitignore` file.

---

### 3. Install Docker and start the LiveKit server

1. **Install Docker**  
   Download and install from [docker.com](https://www.docker.com/products/docker-desktop/).

2. **Start LiveKit server in Docker**  
   Open a **Docker terminal** (or any terminal with Docker available) and run:

   ```bash
   docker run --rm -p 7880:7880 -p 7881:7881 -e LIVEKIT_KEYS="devkey: secretsecretsecretsecretsecretsecret" livekit/livekit-server --dev --bind 0.0.0.0
   ```

   Keep this terminal open so the server keeps running.  
   The server will be available at `http://localhost:7880` (or your machine’s IP on port 7880).

   > **Note:** The API key and secret in `LIVEKIT_KEYS` must match `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in your `.env` file.

---

### 4. Run the LiveKit agent

In a **new terminal**, go to the project folder and run:

```bash
python livekit_agent.py dev
```

Wait until you see something like **"Agent starting..."** and **"Connected to room"** (after you join a room). Leave this terminal running.

---

### 5. Generate a token

In **another terminal**, from the project folder:

```bash
python generate_token.py
```

Copy the **entire token** (long JWT string) that is printed.

---

### 6. Join the meeting and ask your questions

1. Open the **LiveKit Meet** (or LiveKit Playground) in your browser:  
   - **LiveKit Meet:** https://meet.livekit.io  
   - Or use the LiveKit CLI / any client that supports joining with a token.

2. When prompted, paste the **room name**: `test-room`  
   and the **token** you got from `generate_token.py`.

3. Allow microphone access, join the room, and start speaking.  
   The agent will:
   - Listen and transcribe your speech  
   - Analyze stress from your voice and text  
   - Reply with supportive responses  
   - Transfer to a human if you ask (e.g. “I want to talk to a human”)

4. Ask your questions or describe how you feel; the agent will respond accordingly.

---

## Quick reference

| Step | Where        | Command / Action |
|------|--------------|-------------------|
| 1    | Project terminal | `pip install -r requirements.txt` |
| 2    | Project root     | Create `.env` with `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GROQ_API_KEY` |
| 3    | Docker terminal  | `docker run --rm -p 7880:7880 -p 7881:7881 -e LIVEKIT_KEYS="devkey: secretsecretsecretsecretsecretsecret" livekit/livekit-server --dev --bind 0.0.0.0` |
| 4    | Project terminal | `python livekit_agent.py dev` |
| 5    | Project terminal | `python generate_token.py` → copy token |
| 6    | Browser / client | Join room `test-room` with the token and ask your questions |

---

## Project structure (main files)

- **`livekit_agent.py`** – LiveKit voice agent: connects to room, handles audio, stress detection, and responses  
- **`generate_token.py`** – Generates a JWT to join the room `test-room`  
- **`response_engine.py`** – Generates supportive text replies (e.g. via LLM)  
- **`text_sentiment.py`** – Text-based sentiment analysis  
- **`sentiment_pipeline.py`** – Audio-based analysis (e.g. stress from voice)  
- **`stress_trigger.py`** – Combines signals to decide when to treat the user as stressed  
- **`text_to_speech.py`** – Converts agent replies to speech  
- **`handoff.py`** – Handoff to human when requested  

---

## Troubleshooting

- **Agent doesn’t connect**  
  Ensure the LiveKit server is running in Docker and that `livekit_agent.py dev` is using the same URL (default: local server). Check for firewall or port conflicts.

- **Invalid token**  
  Make sure the API key and secret in `generate_token.py` match the `LIVEKIT_KEYS` used in the `docker run` command.

- **No audio / no response**  
  Allow microphone access in the browser and ensure you’re in the same room as the agent (`test-room`). Check the agent terminal for errors.

- **Docker not found**  
  Install Docker Desktop and ensure the Docker daemon is running before running the `docker run` command.
