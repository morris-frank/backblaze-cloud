// basic functions..............................................................
function ready(fn) {
    if (document.readyState != 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}
//..............................................................................

function replace_preview(id, new_src) {
    let root = document.getElementById(id);
    let img_elem = root.getElementsByClassName("preview")[0].getElementsByTagName("img")[0]
    img_elem.src = new_src;
}

// web-sockets..................................................................
function setup_update_socket() {
    let ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/updates');

    ws.onmessage = function (event) {
        let update = JSON.parse(event.data);

        switch(update.type) {
            case "preview":
                replace_preview(update.id, update.url);
                break;
            default:
                console.log("Received unkown update type.")
        }
    };
}
// .............................................................................


function main() {
    console.log("start");
    setup_update_socket();
}

ready(main);