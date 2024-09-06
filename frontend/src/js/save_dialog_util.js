const {shell} = require('electron')

const ipc = require('electron').ipcRenderer;

const btn = document.getElementById('download')

btn.addEventListener('click', function (event) {
    ipc.send('open-file-dialog-for-file');
}
)

ipc.on('selected-file', function (event, dir) {
    console.log(dir)
    fetch('http://localhost:5000/saveToFolder', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      output_folder_path: dir
    })
  })
  .then(response => {
      return response.json()
    })
    .then(data => {
        console.log(data)
        alert_elem = document.getElementById('alert');
        open_folder_elem = document.getElementById('folder_open_button');
        alert_text = document.getElementById('alert-text');
        alert_text.textContent = data.message;
        if (data.status === 'error'){
            alert_elem.className = 'alert alert-danger'
            open_folder_elem.className = 'btn btn-primary disabled'
        } else {
            alert_elem.className = 'alert alert-success'
            open_folder_elem.className = 'btn btn-primary'
            open_folder_elem.onclick = function() { open_output_folder(data.output_folder_path)};
        }

    });
})

function open_output_folder(folder_path){
  shell.openPath(folder_path)
}