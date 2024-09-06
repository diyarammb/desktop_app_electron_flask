// let keyword_list;
function handleFileSelection() {
  const fileInput = document.getElementById('uploadMultipleFiles');
  const files = fileInput.files;
  displayFileNames(files);
}
function storeMultipleXlsxFile() {
  const fileInput = document.getElementById('uploadMultipleFiles');
  const files = fileInput.files;
  const file_data = files.length
  if (file_data == 0) {
    // alert("Kindly Select one File")
    document.getElementById('fileNamesDisplay').innerHTML='<span style="color:red; margin-left:60px"> Kindly Select one File</span>'
  } else {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files[]', file);}
    fetch('http://localhost:5000/upload', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        inputFiles = data.data;
        storeDncXlsxFile()
        console.log(inputFiles)
      })
      .catch(error => {
        console.error('Error uploading files:', error);
      }); }
}
function displayFileNames(files) {
  const fileNamesDisplay = document.getElementById('fileNamesDisplay');
  fileNamesDisplay.innerHTML = '';
  const fileList = document.createElement('div');
  fileList.className = 'row'
  for (const file of files) {
    const listItem = document.createElement('span');
    listItem.className = 'col-xs-6 m-2'
    listItem.textContent = file.name;
    fileList.appendChild(listItem);
  }
  fileNamesDisplay.appendChild(fileList);
}
function newElement() {
  var li = document.createElement("li");
  li.id='litxt'
  var inputValue = document.getElementById("myInput").value;
  var t = document.createTextNode(inputValue);
  li.appendChild(t);
  document.getElementById("myUL").appendChild(li);
  document.getElementById("myInput").value = "";
  var span = document.createElement("SPAN");
  var txt = document.createTextNode("\u00D7");
  span.className = "close";
  span.appendChild(txt);
  li.appendChild(span);
  var close = document.getElementsByClassName("close");
  for (i = 0; i < close.length; i++) {
    close[i].onclick = function () {
      var div = this.parentElement;
      div.style.display = "none";
    }
  }
}
function sendKeywordListData() {
  const listItems = document.querySelectorAll('#myUL li');
  let listTextArray = [];
  listItems.forEach((li) => { 
    const liText = li.childNodes[0].nodeValue.trim(); 
    listTextArray.push(liText);
  });
  const mode = document.getElementById('color_mode').checked;
  const keywordFilter = document.getElementById('keyword').checked;
  const extractDuplicates = document.getElementById('extractDuplicates').checked;
  const removeDNCRecords = document.getElementById('removeDNCRecords').checked;
  const combineAllLists = document.getElementById('combineAllLists').checked;
  const removeOldProcessedRecords = document.getElementById('removeOldProcessedRecords').checked;
  fetch('http://localhost:5000/send_keyword_list_data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      keywordList: listTextArray,
      mode: mode,
      keyword: keywordFilter,
      extractDuplicates: extractDuplicates,
      removeDNCRecords: removeDNCRecords,
      combineAllLists: combineAllLists,
      removeOldProcessedRecords: removeOldProcessedRecords
    }),
  })
    .then(response => response.json())
    .then(result => {
      
      console.log('Server response:', result);
      window.location = '../html/column-selection.html'
    })
    .catch(error => {
      console.error('Error sending data to server:', error);
    });
}
function storeDncXlsxFile() {
  var fileInput = document.getElementById('fileInput');
  var file = fileInput.files[0];
  if (fileInput.files.length == 0) {
    window.location = '../html/settings.html'
  } else {
    var formData = new FormData();
    formData.append('file', file);
    fetch('http://localhost:5000/upload_dnc_files', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        console.log('Success:', data);
        window.location = '../html/settings.html'
      })
      .catch(error => {
        console.error('Error:', error);
      });
  }}
function RemoveKey() {
  console.log('delete item')
  var dataList = document.getElementById('dataList');
  dataList.innerHTML = ''
}