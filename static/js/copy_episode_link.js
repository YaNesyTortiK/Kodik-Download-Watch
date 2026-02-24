let episodeButtons = document.getElementsByClassName("episode-number");
let autoMpvToggle = document.getElementById("auto_mpv_toggle");
let shikimori_id = episodeButtons.length > 0 ? episodeButtons[0].getAttribute("data-shikimori-id") : null;

// Инициализация тумблера
if (autoMpvToggle) {
    const isAuto = localStorage.getItem("autoMPV") === "true";
    autoMpvToggle.checked = isAuto;
    autoMpvToggle.addEventListener("change", (e) => {
        localStorage.setItem("autoMPV", e.target.checked);
    });
}

// Слушатель для кнопок серий
for (let item of episodeButtons) {
    item.addEventListener("click", (e) => {
        const isAuto = localStorage.getItem("autoMPV") === "true";
        if (isAuto) {
            fetchAndOpenMPV(e);
        } else {
            window.location.href = item.getAttribute("data-web-url");
        }
    });
}

if (shikimori_id) {
    load_last_watched(shikimori_id);
}

async function fetchAndOpenMPV(event) {
    const episode = event.currentTarget;
    const notification = document.getElementById("copy-notification");
    
    try {
        if (notification) showNotification(notification, "Запрашиваем ссылку...", 5000);
        
        const shikimori_id = episode.getAttribute("data-shikimori-id");
        const translation_id = episode.getAttribute("data-translation-id");
        const ep_value = episode.value;

        const response = await fetch(`/get_episode/${shikimori_id}/${ep_value}/${translation_id}`);

        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }

        const text = await response.text();
        window.location.href = `mpv://${encodeURIComponent(text)}`;
        
        if (notification) showNotification(notification, "Открываю MPV!", 2000);
        
        save_last_watched(shikimori_id, ep_value, translation_id);
    } catch (err) {
        console.error('Ошибка:', err);
        if (notification) showNotification(notification, "Ошибка открытия :(", 3000);
    }
}

function showNotification(el, text, duration) {
    el.querySelector(".alert").textContent = text;
    el.classList.add("visible");
    if (el.timeout) clearTimeout(el.timeout);
    el.timeout = setTimeout(() => el.classList.remove("visible"), duration);
}

function save_last_watched(shikimori_id, episode, translation_id) {
    const data = JSON.parse(localStorage.getItem("lastEpisodes") || "{}");
    data[shikimori_id] = [episode, translation_id];
    localStorage.setItem("lastEpisodes", JSON.stringify(data));
    highlight_last_watched(shikimori_id, episode, translation_id);
}

function highlight_last_watched(shikimoriId, episode, translationId) {
    for (let btn of episodeButtons) {
        if (btn.getAttribute("data-translation-id") === translationId && btn.value === episode) {
            btn.classList.add("last-watched");
        } else {
            btn.classList.remove("last-watched");
        }
    }
}

function load_last_watched(shikimori_id) {
    const data = JSON.parse(localStorage.getItem("lastEpisodes") || "{}");
    if (data[shikimori_id]) {
        highlight_last_watched(shikimori_id, data[shikimori_id][0], data[shikimori_id][1]);
    }
}
