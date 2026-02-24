let container = document.getElementsByClassName("recently_watch")[0]
let data = JSON.parse(localStorage.getItem("recently_watched") || "[]");
let domain = window.location.hostname
let style = document.body.classList.contains("dark-body") ? "dark-href" : "mb-3"
console.log(style)

for (let item of data){
    let card = document.createElement("a");
    card.classList.add("card");
    card.classList.add(style);
    card.href = `https://${domain}/download/sh/${item[0]}`

    // создаём img
    let img = document.createElement("img");
    img.src = item[2];

    // создаём текстовый элемент
    let text = document.createElement("h6");
    text.textContent = item[1];


    // собираем структуру
    card.appendChild(img);
    card.appendChild(text);

    // вставляем в контейнер
    container.appendChild(card);
}