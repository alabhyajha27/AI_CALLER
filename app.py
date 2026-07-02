from flask import Flask, render_template, send_file
from flask_sock import Sock
import subprocess
import os

from ai_caller import (
    transcribe_audio,
    generate_reply,
    speak
)

app = Flask(__name__)
sock = Sock(app)

# Create recordings folder
os.makedirs("recordings", exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/reply")
def reply_audio():
    return send_file(
        "reply.mp3",
        mimetype="audio/mpeg"
    )


def convert_to_wav():

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", "recordings/input.webm",
            "-ar", "16000",
            "-ac", "1",
            "recordings/input.wav"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("✅ Converted to input.wav")


@sock.route("/ws")
def websocket(ws):

    print("✅ Browser Connected")

    while True:

        data = ws.receive()

        if data is None:

            print("❌ Browser Disconnected")

            break

        # --------------------------
        # AUDIO RECEIVED
        # --------------------------

        if isinstance(data, bytes):

            print("🎤 Audio Received")

            with open("recordings/input.webm", "wb") as f:
                f.write(data)

            print("✅ input.webm saved")

            convert_to_wav()

            # --------------------------
            # Speech To Text
            # --------------------------

            user_text = transcribe_audio(
                "recordings/input.wav"
            )

            print("Candidate:", user_text)

            # --------------------------
            # LLM
            # --------------------------

            reply = generate_reply(user_text)

            print("AI:", reply)

            # --------------------------
            # Text To Speech
            # --------------------------

            speak(reply)

            # Send reply text back to browser
            ws.send(reply)

        else:

            print("Message:", data)


if __name__ == "__main__":
    app.run(debug=True)