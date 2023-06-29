const video = document.querySelector("video");

var socket = io();
let hrf = window.location.href;
let rid = hrf.slice(hrf.slice(0, -5).lastIndexOf('/')+1, -1);

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
    if (event.data.status == 'update_page') {
        window.location.reload();
    }
})
