function appendMessage(msg, type, imageURL = null) {
    const chatlogs = document.getElementById('chatlogs');
    const div = document.createElement('div');
    div.className = `chat-message ${type === 'bot' ? 'bot-msg' : 'user-msg'}`;

    if (type === 'bot') {
        div.innerHTML = `<img src="/static/images/bot.png" class="bot-avatar" alt="Bot"><span>${msg}</span>`;
        speak(msg);
    } else {
        div.innerHTML = `<span>${msg}</span>`;
        if (imageURL) {
            const img = document.createElement('img');
            img.src = imageURL;
            img.className = "chat-image-preview";
            div.appendChild(img);
        }
    }

    chatlogs.appendChild(div);
    chatlogs.scrollTop = chatlogs.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, 'user');
    input.value = "";

    fetch(`/get_response/?msg=${encodeURIComponent(message)}`)
        .then(res => res.json())
        .then(data => appendMessage(data.reply, 'bot'))
        .catch(() => appendMessage("Oops! Something went wrong.", 'bot'));
}

document.getElementById('imageInput').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        appendMessage("Uploaded image:", "user", e.target.result);
    };
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append("image", file);

    appendMessage("Analyzing your image...", 'bot');

    fetch(`/analyze_image/`, {
        method: 'POST',
        body: formData,
        headers: { "X-CSRFToken": getCookie("csrftoken") }
    })
    .then(res => res.json())
    .then(data => appendMessage(data.reply, 'bot'))
    .catch(() => appendMessage("Couldn't analyze the image.", 'bot'));
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function speak(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text.replace(/<[^>]*>?/gm, ''));
        utterance.lang = 'en-US';
        speechSynthesis.speak(utterance);
    }
}

// Voice recognition
const micBtn = document.getElementById("micBtn");
let recognition;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
        recognition.start();
        micBtn.classList.add("recording");
    });

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("userInput").value = transcript;
        sendMessage();
    };

    recognition.onend = function () {
        micBtn.classList.remove("recording");
    };

    recognition.onerror = function () {
        micBtn.classList.remove("recording");
        appendMessage("Sorry, I couldn't hear you clearly.", 'bot');
    };
} else {
    micBtn.disabled = true;
    micBtn.title = "Voice input not supported in your browser.";
}
