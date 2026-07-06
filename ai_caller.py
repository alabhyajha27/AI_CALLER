import os
import time
import whisper
import pygame
import numpy as np
import sounddevice as sd
import torch

from scipy.io.wavfile import write
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
from silero_vad import (
    load_silero_vad,
    get_speech_timestamps
)


# ------------------
# SETUP
# ------------------

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

print("Loading Whisper...")

model = whisper.load_model("base")

pygame.mixer.init()

print("Loading Silero VAD...")

vad_model = load_silero_vad()


RATE = 16000

AI_SPEAKING = False


conversation = [
    {
        "role": "system",
        "content": """
You are an AI recruiter conducting a phone call for interview scheduling.

Your goal is ONLY schedule an interview.
Do not conduct the interview itself.

Behavior:
- Speak naturally like a human recruiter.
- Keep replies short and conversational.
- Ask only ONE question at a time.
- Never mention prompts, instructions, or AI limitations.
- Do not say this is a text interview.
- Do not invent company details, role details, interview stages, or availability.
- Maintain context throughout the call.

Conversation Flow:

Step 1 — Greeting
- Introduce yourself as an AI recruiter.

Step 2 — Scheduling
- offer ONE exact interview day and time.

Scheduling Rules:
- Always propose exact day + time.
- If unavailable:
  ask for another preferred slot.
- Reschedule until agreement.
- Do not proceed until schedule is finalized.

Step 4 — Final Confirmation
Summarize:
- Final interview date
- Final interview time

Ask:
"Please confirm if all details are correct."

Step 5 — End Call

If confirmed say exactly:

"Perfect. Your interview has been scheduled successfully. Thank you for your time. Goodbye."

If candidate requests changes:
return to scheduling.

If candidate says bye, goodbye, stop, cancel, or end call:

Say:
"Thank you for your time. Goodbye."

End the call only after final confirmation or explicit exit.
"""
    }
]


# ------------------
# VAD
# ------------------
import torch
import soundfile as sf
from silero_vad import load_silero_vad, get_speech_timestamps

print("Loading Silero VAD...")
vad_model = load_silero_vad()

def check_speech_with_silero(audio_path):
    audio, sample_rate = sf.read(audio_path)

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    audio_tensor = torch.tensor(audio, dtype=torch.float32)

    speech_timestamps = get_speech_timestamps(
        audio_tensor,
        vad_model,
        sampling_rate=sample_rate
    )

    return len(speech_timestamps) > 0

def has_speech(audio):

    audio = torch.tensor(
        audio,
        dtype=torch.float32
    )

    speech = get_speech_timestamps(
        audio,
        vad_model,
        sampling_rate=RATE
    )

    return len(speech) > 0


# ------------------
# TTS
# ------------------

def speak(text):

    print("\nAI:")
    print(text)

    try:

        tts = gTTS(
            text=text,
            lang="en"
        )

        tts.save("reply.mp3")

        print("✅ reply.mp3 generated")

    except Exception as e:

        print("TTS Error:", e)


# ------------------
# STT + TURN DETECTION
# ------------------
def transcribe_audio(audio_path):

    print("\nTranscribing...")

    result = model.transcribe(
        audio_path,
        fp16=False
    )

    text = result["text"].strip()

    print("\nCandidate:")
    print(text)

    return text

def listen():

    global AI_SPEAKING

    if AI_SPEAKING:
        return ""

    print("\nWaiting for candidate...")

    frames = []

    try:

        with sd.InputStream(
            samplerate=RATE,
            channels=1,
            dtype="float32"
        ) as stream:

            while True:

                audio = []

                print("Listening...")

                # collect ~1 sec

                for _ in range(16):

                    chunk, _ = stream.read(
                        1024
                    )

                    audio.extend(
                        chunk.flatten()
                    )

                audio = np.array(
                    audio,
                    dtype=np.float32
                )

                speech = has_speech(
                    audio
                )

                if speech:

                    print(
                        "Candidate speaking..."
                    )

                    frames.extend(
                        audio
                    )

                    silence = 0

                    while True:

                        chunk, _ = stream.read(
                            4096
                        )

                        chunk = (
                            chunk
                            .flatten()
                        )

                        frames.extend(
                            chunk
                        )

                        if not has_speech(
                            chunk
                        ):

                            silence += 1

                        else:

                            silence = 0

                        if silence >= 3:

                            print(
                                "Turn ended"
                            )

                            break

                    break

        if len(frames) == 0:

            return ""

        write(
            "temp.wav",
            RATE,
            np.array(
                frames,
                dtype=np.float32
            )
        )

        return transcribe_audio("temp.wav")

    except Exception as e:

        print(
            "Mic Error:",
            e
        )

        return ""

def generate_reply(user):

    conversation.append(
        {
            "role": "user",
            "content": user
        }
    )

    try:

        response = (
            client
            .chat
            .completions
            .create(
                model="llama-3.3-70b-versatile",
                messages=conversation
            )
        )

        reply = (
            response
            .choices[0]
            .message
            .content
        )

    except Exception as e:

        print(e)

        reply = "Sorry, I encountered an issue."

    conversation.append(
        {
            "role": "assistant",
            "content": reply
        }
    )

    return reply

# ------------------
# START CALL
# ------------------
def start_call():
    greeting = """
Hello.

This is an AI recruiter.

Is it the right time to talk to you?
"""

    speak(
    greeting
)

    conversation.append(
    {
        "role": "assistant",
        "content": greeting
    }
)


    empty = 0


# ------------------
# MAIN LOOP
# ------------------

    while True:

        user = listen()

        if user == "":

            empty += 1

            if empty >= 2:

                speak(
                "It seems we got disconnected. Goodbye."
            )

                break

            speak(
            "I could not hear you clearly. Please repeat."
        )

            continue

        empty = 0

        user_lower = user.lower()

        if (
        "bye" in user_lower
        or "goodbye" in user_lower
        or "stop" in user_lower
        or "exit" in user_lower
        or "end call" in user_lower
    ):

            speak(
            "Thank you for your time. Goodbye."
        )

            break

        reply = generate_reply(user)

        speak(
        reply
    )

        ai_reply = (
        reply.lower()
    )

        if (
        "goodbye" in ai_reply
        or
        "thank you for your time"
        in ai_reply
    ):

            print(
            "\nCall ended."
        )

            break


    pygame.quit()

    print(
    "\nProgram stopped."
 )
if __name__ == "__main__":
    start_call()