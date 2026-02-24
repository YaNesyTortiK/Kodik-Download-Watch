let numbers = document.getElementsByClassName("episode-number")
let shikimori_id = numbers[0].getAttribute("data-shikimori-id")


for (let item of numbers){

    item.addEventListener("click", fetchAndCopy)
}
load_last_watched(shikimori_id)

async function fetchAndCopy() {
    try {
        let episode = event.currentTarget;
        let copy_alert = episode.parentElement.parentElement.getElementsByClassName("copied")[0]
        fadeOut(copy_alert,"Запрашиваем ссылку!", 50000);
        let shikimori_id = episode.getAttribute("data-shikimori-id")
        console.log(copy_alert)
        let translation_id = episode.getAttribute("data-translation-id")
        // Отправляем запрос на сервер
        const response = await fetch(`/get_episode/${shikimori_id}/${episode.value}/${translation_id}`);

        if (!response.ok) {
            throw new Error(`Ошибка запроса: ${response.status} ${response.statusText}`);
        }

        const text = await response.text();
        window.location.href = `mpv://${escape(text)}`
        // Копируем в буфер обмена
        // await navigator.clipboard.writeText(text);

        fadeOut(copy_alert,"Открываю MPV!", 2000);
        save_last_watched(shikimori_id, episode.value, translation_id)
        update_recently_watched_list(shikimori_id)
    } catch (err) {
        console.error('Не удалось получить или скопировать ответ:', err);
    }
}


function fadeOut(element, text, duration = 300) {
    let start = null;
    element.getElementsByClassName("alert")[0].innerHTML = text
    element.style.visibility = 'visible';
    

    function step(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        const opacity = Math.max(1 - progress / duration, 0);

        element.style.opacity = opacity;

        if (progress < duration) {
            requestAnimationFrame(step);
        } else {
            element.style.opacity = 0;
            element.style.visibility = 'hidden';
        }
    }

    requestAnimationFrame(step);
}

function save_last_watched(shikimori_id, episode, translation_id){
    const data = JSON.parse(localStorage.getItem("lastEpisodes") || "{}");
    data[shikimori_id] = [episode, translation_id];
    localStorage.setItem("lastEpisodes", JSON.stringify(data));
    load_last_watched(shikimori_id)

}

function update_recently_watched_list(shikimori_id){
    let imglink = document.getElementsByClassName("imglink")[0].getAttribute("src")
    let name = document.getElementsByClassName("anime-title")[0].innerHTML
    let data = JSON.parse(localStorage.getItem("recently_watched") || "[]");

    if (data.length >= 5)
        data.pop()

    data.unshift([shikimori_id, name, imglink])
    localStorage.setItem("recently_watched", JSON.stringify(data))
}

function load_last_watched(shikimori_id) {
    const data = JSON.parse(localStorage.getItem("lastEpisodes") || "{}");
    for (let item of numbers){
        if (item.getAttribute("data-translation-id") === data[shikimori_id][1] && item.value === data[shikimori_id][0] ){
            item.classList.add("last-watched")
            break
        }

    }

}
