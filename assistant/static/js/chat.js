function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    const chatlogs = document.getElementById("chatlogs");

    chatlogs.innerHTML += `<div class="user">${message}</div>`;

    fetch(`/get-response?msg=${encodeURIComponent(message)}`)
        .then(res => res.json())
        .then(data => {
            chatlogs.innerHTML += `<div class="bot">${data.reply}</div>`;
            input.value = "";
            chatlogs.scrollTop = chatlogs.scrollHeight;
        });
}
