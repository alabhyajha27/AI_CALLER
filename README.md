# AI Recruiter Voice Caller

An AI-powered voice calling application that conducts interview scheduling conversations through a web-based interface. The system captures the candidate's voice, transcribes speech into text, generates contextual responses using a Large Language Model (LLM), converts the generated response into speech, and streams it back to the user through the browser.

---

## Features

- Web-based voice interaction
- Browser microphone recording
- Speech-to-Text using OpenAI Whisper
- AI-driven conversation using Groq (Llama 3.3 70B Versatile)
- Text-to-Speech using Google Text-to-Speech (gTTS)
- Real-time chat history
- WebSocket-based communication
- Browser audio playback
- Modular STT → LLM → TTS pipeline

---

## Technology Stack

### Backend

- Python
- Flask
- Flask-Sock (WebSockets)

### Artificial Intelligence

- OpenAI Whisper
- Groq API
- Llama 3.3 70B Versatile

### Audio Processing

- Google Text-to-Speech (gTTS)
- FFmpeg

### Frontend

- HTML
- CSS
- JavaScript
- WebSocket API
- MediaRecorder API

---

## Project Structure

```text
ai-caller/
│
├── app.py                     # Flask application
├── ai_caller.py               # STT → LLM → TTS pipeline
├── requirements.txt
├── .env
│
├── recordings/
│   ├── input.webm
│   └── input.wav
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── script.js
│
└── reply.mp3
```

---

## System Architecture

```text
Browser Microphone
        │
        ▼
MediaRecorder API
        │
        ▼
WebSocket
        │
        ▼
Flask Server
        │
        ▼
FFmpeg
(WebM → WAV)
        │
        ▼
OpenAI Whisper
(Speech-to-Text)
        │
        ▼
Groq Llama 3.3 70B
(Response Generation)
        │
        ▼
Google Text-to-Speech
(Text-to-Speech)
        │
        ▼
reply.mp3
        │
        ▼
Browser Audio Playback
```

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/<your-username>/<repository-name>.git

cd <repository-name>
```

### Create a Virtual Environment

```bash
python -m venv venv
```

#### Windows

```bash
venv\Scripts\activate
```

#### macOS / Linux

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install FFmpeg

Download and install FFmpeg and ensure it is available in your system PATH.

Verify the installation:

```bash
ffmpeg -version
```

### Configure Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
```

---

## Running the Application

Start the Flask server:

```bash
python app.py
```

Open the application in your browser:

```
http://127.0.0.1:5000
```

---

## Workflow

1. Launch the application.
2. Connect to the server.
3. Record a voice response using the browser microphone.
4. The recorded audio is transmitted to the backend.
5. Whisper converts speech into text.
6. Groq Llama generates a contextual response.
7. Google Text-to-Speech converts the response into audio.
8. The generated response is played back in the browser.
9. Continue the conversation as needed.

---

## Current Limitations

- Manual recording termination
- Browser-based recording using MediaRecorder
- Single conversation session
- No automatic turn detection
- No streaming speech recognition

---

## Future Enhancements

- Automatic turn detection using Silero Voice Activity Detection (VAD)
- Real-time streaming transcription
- Faster-Whisper integration
- Speaker interruption (Barge-in)
- Automatic interview scheduling workflow
- Browser-side Voice Activity Detection
- Multi-language support
- Production-ready deployment
- Conversation memory and session persistence

---

## License

This project is intended for educational and research purposes. Modify and extend it as required for your use case.
