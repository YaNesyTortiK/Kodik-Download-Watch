const video = document.querySelector("video");
const copy_link_btn = document.querySelector('.copy_link');
const create_qr_btn = document.querySelector('.create_qr');

var socket = io();
let hrf = window.location.href;
let rid = hrf.slice(hrf.slice(0, -5).lastIndexOf('/')+1, -1);

let qrCode;

video.onpause = function() {
    socket.emit("broadcast", {data: {'status': 'paused', 'time': video.currentTime}, rid: rid})
}

video.onplay = function() {
    socket.emit("broadcast", {data: {'status': 'playing', 'time': video.currentTime}, rid: rid})
}

socket.on('connect', function() {
    socket.emit('join', {data: 'I\'m connected!', rid: rid});
});

socket.on('message', (event) => {
    // console.log(`[message] Данные получены с сервера: ${event.data.status}, ${event}`);
    if (event.data.status == 'loading') {
        video.currentTime = event.data.time;
        video.pause();
    }
    if (event.data.status == 'playing') {
        video.currentTime = event.data.time;
        video.play();
    }
    if (event.data.status == 'paused') {
        video.currentTime = event.data.time;
        video.pause();
    }
    if (event.data.status == 'skipping') {
        video.currentTime = event.data.time;
    }
    if (event.data.status == 'update_page') {
        window.location.reload();
    }
})

copy_link_btn.addEventListener("click", () => {
    navigator.clipboard.writeText(hrf)
        .then(() => {
        if (copy_link_btn.textContent !== 'Скопировано!') {
            const originalText = copy_link_btn.textContent;
            copy_link_btn.textContent = 'Скопировано!';
            setTimeout(() => {
                copy_link_btn.textContent = originalText;
            }, 1500);
        }
        })
        .catch(err => {
        console.log('Something went wrong', err);
        })
});

function generateQrCode(qrContent) {
    return new QRCode("qr_code", {
        text: qrContent,
        width: 256,
        height: 256,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H,
    });
}

create_qr_btn.addEventListener("click", function (event) {
    if (qrCode == null) {
        qrCode = generateQrCode(hrf);
    } else {
        qrCode.makeCode(hrf);
    }
    document.getElementById("qr_code_container").style = "background-color: white; height: 300px; width: 300px; display: flex; align-items: center;justify-content: center;"
});

function skip_left() {
    if (video.currentTime - 80 > 0) {
        video.currentTime = video.currentTime-80
    } else {
        video.currentTime = 0
    }
    socket.emit("broadcast", {data: {'status': 'skipping', 'time': video.currentTime}, rid: rid})
};
function skip_right() {
    if (video.currentTime + 80 < video.duration) {
        video.currentTime = video.currentTime+80
    } else {
        video.currentTime = video.duration
    }
    socket.emit("broadcast", {data: {'status': 'skipping', 'time': video.currentTime}, rid: rid})
};