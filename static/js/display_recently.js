let container = document.querySelector(".recently_watch");
let data = JSON.parse(localStorage.getItem("recentlyWatched") || "[]");

if (data.length === 0)
    container.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center;">У вас пока нет просмотренных аниме.</p>';
else {
    for (let item of data) {
        let card = document.createElement("a");
        card.classList.add("card");
        card.href = `/download/sh/${item["id"]}/`;

        let img = document.createElement("img");
        img.src = item["img-link"];
        img.loading = "lazy";

        let textWrap = document.createElement("div");
        let text = document.createElement("h6");
        text.textContent = item["name"];

        card.appendChild(img);
        card.appendChild(text);
        container.appendChild(card);
    }
}