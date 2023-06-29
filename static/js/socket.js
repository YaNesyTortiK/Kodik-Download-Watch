var socket = io();
console.log("Socket script initialized")
let hrf = window.location.href;
let rid = hrf.slice(hrf.slice(0, -5).lastIndexOf('/')+1, -1);

const video = document.querySelector("video");

socket.on('connect', function() {
    socket.emit('join', {data: 'I\'m connected!', rid: rid});
});

socket.on('my event', (event) => {
    console.log(`[my event] Данные получены с сервера: ${event.data}`);
})

socket.on('answer', (event) => {
    console.log(`[answer] Данные получены с сервера: ${event.data}`);
})

socket.on('broadcast', (event) => {
    console.log(`[broadcast] Данные получены с сервера: ${event.data}`);
})

socket.on('join', (event) => {
    console.log(`[join] Данные получены с сервера: ${event.data}`);
})


socket.on('message', (event) => {
    console.log(`[message] Данные получены с сервера: ${event.data}`);
})


socket.onmessage = function(event) {
    alert(`[message] Данные получены с сервера: ${event.data}`);
};