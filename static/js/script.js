const connectBtn = document.getElementById("connectBtn");
const micBtn = document.getElementById("micBtn");
const stopBtn = document.getElementById("stopBtn");
const status = document.getElementById("status");

let socket;
let mediaRecorder;
let audioChunks = [];

// ------------------------------------
// ADD MESSAGE TO CHAT
// ------------------------------------

function addMessage(sender, text) {

    const chat = document.getElementById("chat");

    const message = document.createElement("div");
    message.className = "message";

    if (sender === "AI") {

        message.innerHTML = `
            <div class="ai">🤖 AI</div>
            <div class="text">${text}</div>
        `;

    } else {

        message.innerHTML = `
            <div class="user">👤 Candidate</div>
            <div class="text">${text}</div>
        `;

    }

    chat.appendChild(message);
    chat.scrollTop = chat.scrollHeight;
}

// ------------------------------------
// CONNECT
// ------------------------------------

connectBtn.onclick = () => {

    socket = new WebSocket("ws://127.0.0.1:5000/ws");

    socket.onopen = () => {

        console.log("Connected");

        status.innerText = "🟢 Connected";

        micBtn.disabled = false;

    };

    socket.onmessage = (event) => {

        console.log("AI:", event.data);

        addMessage("AI", event.data);

        status.innerText = "🔊 AI Speaking";

        const audio = new Audio("/reply?" + Date.now());

        audio.play().catch(err => console.log(err));

        audio.onended = () => {

            status.innerText = "🟢 Connected";

        };

    };

    socket.onclose = () => {

        status.innerText = "🔴 Disconnected";

        micBtn.disabled = true;
        stopBtn.disabled = true;

    };

};

// ------------------------------------
// START RECORDING
// ------------------------------------

micBtn.onclick = async () => {

    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
    });

    audioChunks = [];

    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {

        audioChunks.push(event.data);

    };

    mediaRecorder.onstop = () => {

        const audioBlob = new Blob(audioChunks, {
            type: "audio/webm"
        });

        addMessage(
            "Candidate",
            "🎤 Voice Message"
        );

        status.innerText = "🧠 AI Thinking...";

        socket.send(audioBlob);

    };

    // THIS IS IMPORTANT
    mediaRecorder.start();

    status.innerText = "🎤 Recording...";

    micBtn.disabled = true;
    stopBtn.disabled = false;

};

// ------------------------------------
// STOP RECORDING
// ------------------------------------

stopBtn.onclick = () => {

    mediaRecorder.stop();

    micBtn.disabled = false;
    stopBtn.disabled = true;

};