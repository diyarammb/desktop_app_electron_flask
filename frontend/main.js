
const electron = require('electron');
const { app, BrowserWindow } = electron;
const path = require('path');
const os = require('os');
const { dialog } = require('electron');
const ipc = require('electron').ipcMain
let mainWindow;

app.on('ready', () => {
    sendToPython();
    createWindow();
});

function createWindow() {
    mainWindow = new BrowserWindow(
        {
            width: 800,
            height: 600,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                // enableRemoteModule: true
            }
        }
    );
    mainWindow.loadFile(path.join(__dirname, 'src', 'html', 'upload.html'));
}
const find = require('find-process');
const child_process = require('child_process');


function sendToPython() {
    var python = require("child_process").execFile("src/App.exe");
    python.stdout.on("data", function (data) {
        console.log(data)
    });

    python.stderr.on("data", (data) => {
        console.error(`stderr: ${data}`);
        console.log(`stderr: ${data}`);
    });

    python.on("close", (code) => {
        console.log(`child process exited with code ${code}`);
    });
    // TODO: Test the close app functionality

}
app.on('window-all-closed', () => {
    find('name', 'App.exe', true)
        .then(function (list) {
            let pid;
            console.log('there are %s App.exe process(es)', list.length);
            if (list.length > 0) {
                list.forEach((list_item) => {
                    pid = list_item.pid;
                    console.log('App.exe is running using the pid: %s', pid);
                    process.kill(pid);
                })
            }
        })

    app.quit();
});

ipc.on('open-file-dialog-for-file', function (event) {

    if (os.platform() === 'linux' || os.platform() === 'win32') {
        console.log(os.platform())
        dialog.showOpenDialog({
            properties: ["openDirectory"],
        }).then(
            (files) => {
                console.log(files)
                if (files) {
                    event.sender.send('selected-file', files.filePaths[0])
                }
            }
        )
    }

    // dialog.showOpenDialog({
    //     properties: ["openFile"],
    // }, function(dir){
    //     if (dir){
    //         event.sender.send('selected-dir', dir)
    //     }
    // })
})