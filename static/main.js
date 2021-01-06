// basic functions..............................................................
function ready(fn) {
    if (document.readyState != 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}
//..............................................................................


// replace contents with updates functions......................................
function replace_preview(id, new_src) {
    let root = document.getElementById(id);
    if (root != null) {
        let img_elem = root.getElementsByClassName("preview")[0].getElementsByTagName("img")[0]
        img_elem.src = new_src;
    }
}

function replace_folder_contents(path, new_contents) {
    for (const folder of document.getElementsByClassName("folder")) {
        if (folder.dataset.path == path) {
            console.log("Updated folder contents for path " + path);
            folder.innerHTML = new_contents;
        }
    }
}
//..............................................................................

// web-sockets..................................................................
function setup_update_socket() {
    let ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/updates');

    ws.onmessage = function (event) {
        let update = JSON.parse(event.data);

        switch (update.type) {
            case "preview":
                replace_preview(update.id, update.url);
                break;
            case "folder":
                replace_folder_contents(update.path, update.content);
                break;
            default:
                console.log("Received unkown update type.")
        }
    };
}

function setup_request_socket() {
    let ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/update');
    
    ws.onopen = function(event) {
        // Now if the user stays on the page for a second, we load the new contents
        setTimeout(function () {
            for (const folder of document.getElementsByClassName("folder")) {
                var data = { "path": folder.dataset.path, "type": "folder" };
                ws.send(JSON.stringify(data));
            }
        }, 2000);
    };
}
// .............................................................................


function main() {
    setup_update_socket();
    setup_request_socket();
}

ready(main);