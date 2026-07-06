const startBtn = document.getElementById("start-btn");
const endBtn = document.getElementById("end-btn");
const status = document.getElementById("status");
const chatBox = document.getElementById("chat-box");

let socket = null;
let mediaRecorder = null;
let audioChunks = [];
let currentStream = null;

let isRecording = false;
let isAISpeaking = false;
let callActive = false;


// ------------------------------------
// ADD MESSAGE
// ------------------------------------

function addMessage(sender, text) {
    if (chatBox.querySelector(".empty-state")) {
        chatBox.innerHTML = "";
    }

    const message = document.createElement("div");

    if (sender === "AI") {
        message.className = "message ai-message";
        message.innerHTML = `
            <strong>AI</strong>
            <div class="text">${text}</div>
        `;
    } else {
        message.className = "message user-message";
        message.innerHTML = `
            <strong>Candidate</strong>
            <div class="text">${text}</div>
        `;
    }

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}


// ------------------------------------
// START CALL
// ------------------------------------

startBtn.onclick = async () => {
    callActive = true;

    startBtn.disabled = true;
    endBtn.disabled = false;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        socket = new WebSocket("ws://127.0.0.1:5000/ws");

        socket.onopen = () => {
            console.log("Connected");
            status.innerText = "Listening...";
            startRecording();
        };

        socket.onmessage = handleSocketMessage;

        socket.onclose = () => {
            console.log("Disconnected");

            callActive = false;
            isRecording = false;
            isAISpeaking = false;

            status.innerText = "Disconnected";

            startBtn.disabled = false;
            endBtn.disabled = true;
        };

    } else {
        startRecording();
    }
};


// ------------------------------------
// HANDLE SERVER MESSAGE
// ------------------------------------

function handleSocketMessage(event) {
    const message = event.data;
    console.log(message);

    if (message.startsWith("END_CALL||")) {
        const reply = message.replace("END_CALL||", "");

        addMessage("AI", reply);
        status.innerText = "AI Speaking...";
        isAISpeaking = true;

        const audio = new Audio("/reply?" + Date.now());

        audio.onended = () => {
            isAISpeaking = false;
            callActive = false;

            status.innerText = "Call Ended";

            startBtn.disabled = false;
            endBtn.disabled = true;

            stopRecordingIfActive();

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.close();
            }
        };

        audio.play();
        return;
    }

    if (message.startsWith("AI||")) {
        const reply = message.replace("AI||", "");

        addMessage("AI", reply);
        status.innerText = "AI Speaking...";
        isAISpeaking = true;

        const audio = new Audio("/reply?" + Date.now());

        audio.onended = () => {
            isAISpeaking = false;

            if (callActive) {
                status.innerText = "Listening...";
                startRecording();
            }
        };

        audio.play();
        return;
    }
}


// ------------------------------------
// RECORD AUDIO
// ------------------------------------

async function startRecording() {
    if (!callActive || isRecording || isAISpeaking) {
        return;
    }

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioChunks = [];

        mediaRecorder = new MediaRecorder(currentStream);
        isRecording = true;

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            isRecording = false;

            if (!callActive) {
                stopStream();
                return;
            }

            const blob = new Blob(audioChunks, {
                type: "audio/webm"
            });

            console.log("Audio blob size:", blob.size);

            stopStream();

            if (blob.size < 1000) {
                status.innerText = "No speech detected. Listening again...";
                setTimeout(() => {
                    if (callActive) startRecording();
                }, 500);
                return;
            }

            addMessage("Candidate", "Voice message sent");
            status.innerText = "Processing...";

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(blob);
            }
        };

        mediaRecorder.start();
        status.innerText = "Recording... Speak now";

        detectSilenceAndStop(currentStream);

    } catch (error) {
        console.error("Microphone error:", error);
        status.innerText = "Microphone access denied or unavailable.";

        startBtn.disabled = false;
        endBtn.disabled = true;
        callActive = false;
    }
}


// ------------------------------------
// SILENCE DETECTION
// ------------------------------------

function detectSilenceAndStop(stream) {
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();

    source.connect(analyser);
    analyser.fftSize = 2048;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    let hasSpoken = false;
    let silenceStart = null;

    const silenceThreshold = 10;
    const silenceDuration = 1500;

    function checkAudio() {
        if (!mediaRecorder || mediaRecorder.state !== "recording") {
            audioContext.close();
            return;
        }

        analyser.getByteFrequencyData(dataArray);

        const volume =
            dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

        if (volume > silenceThreshold) {
            hasSpoken = true;
            silenceStart = null;
        } else if (hasSpoken) {
            if (!silenceStart) {
                silenceStart = Date.now();
            }

            if (Date.now() - silenceStart > silenceDuration) {
                mediaRecorder.stop();
                return;
            }
        }

        requestAnimationFrame(checkAudio);
    }

    checkAudio();
}


// ------------------------------------
// END CALL
// ------------------------------------

endBtn.onclick = () => {
    callActive = false;

    status.innerText = "Ending Call...";

    stopRecordingIfActive();

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("END_CALL");
    }

    endBtn.disabled = true;
};


// ------------------------------------
// HELPERS
// ------------------------------------

function stopRecordingIfActive() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }

    stopStream();
}

function stopStream() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}