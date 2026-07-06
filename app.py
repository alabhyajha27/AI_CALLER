from flask import Flask, render_template, send_file
from flask_sock import Sock
import subprocess
import os

from ai_caller import (
    transcribe_audio,
    generate_reply,
    speak,
    has_speech
)

app = Flask(__name__)
sock = Sock(app)

os.makedirs("recordings", exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/reply")
def reply_audio():
    return send_file("reply.mp3", mimetype="audio/mpeg")


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


def check_speech_from_wav():
    import soundfile as sf

    audio, sample_rate = sf.read("recordings/input.wav")

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    try:
        return has_speech(audio, sample_rate)
    except TypeError:
        return has_speech(audio)


@sock.route("/ws")
def websocket(ws):
    print("Browser connected")

    while True:
        data = ws.receive()

        if data is None:
            print("Browser disconnected")
            break

        if data == "END_CALL":
            print("Candidate ended the call.")

            reply = "Thank you for your time. Goodbye."
            speak(reply)

            ws.send("END_CALL||" + reply)
            break

        if isinstance(data, bytes):
            print("Audio received")

            with open("recordings/input.webm", "wb") as f:
                f.write(data)

            convert_to_wav()

            if not check_speech_from_wav():
                ws.send("AI||I could not detect clear speech. Please repeat.")
                continue

            user_text = transcribe_audio("recordings/input.wav")

            if not user_text.strip():
                ws.send("AI||I could not understand that. Please repeat.")
                continue

            print("Candidate:", user_text)

            reply = generate_reply(user_text)
            print("AI:", reply)

            speak(reply)

            end_phrases = [
                "your interview has been scheduled successfully",
                "thank you for your time. goodbye",
                "goodbye"
            ]

            if any(phrase in reply.lower() for phrase in end_phrases):
                ws.send("END_CALL||" + reply)
                break
            else:
                ws.send("AI||" + reply)

        else:
            print("Message:", data)


if __name__ == "__main__":
    app.run(debug=True)