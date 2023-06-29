
const video = document.querySelector("video");

let my_data = {
    "pause": false,
    "play_time": 0,
    "clicked": false,
}

async function getJson() {
    let hrf = window.location.href;
    let url = "/synchronize/"+hrf.slice(hrf.slice(0, -5).lastIndexOf('/')+1);

    my_data['play_time'] = video.currentTime

    let p_bef = my_data['pause']
    my_data['pause'] = video.paused
    if (p_bef != my_data['pause']) {
        my_data['clicked'] = true;
    }

    var res = await fetch(url, {
        method: "POST",
        body: JSON.stringify(my_data),
        headers: {
          "Content-type": "application/json; charset=UTF-8"
        }
      });
    myArray = await res.json();

    my_data['clicked'] = false;
    
    if (myArray['pause'] && !my_data['pause'])  {
        video.currentTime = myArray['play_time']
        my_data['play_time'] = myArray['play_time']
        video.pause();
    } 
    if (!myArray['pause'] && my_data['pause']){
        video.currentTime = myArray['play_time']
        my_data['play_time'] = myArray['play_time']
        video.play();
    }

}

setInterval(getJson, 500)