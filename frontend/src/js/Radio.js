let current_file_index = 0;
let input_files = {};
let input_file_paths = [];
let mode = 'Phone';
let current_file_info;
let current_file_path;
let selected_input_files_column_mapping = {};
let selected_dnc_files_column_mapping = {};
let radio_container = document.getElementById('scrollable-container');
// Lets have something like excel file and columns and also have the file type

let inputFiles;
let currentPage = 0;
let radioContainer = document.getElementById('scrollable-container');
let all_radio_btns;
let radioButtonAndPath = {};
let dataArray;
let dnc_files = {}
let dnc_path

window.onload = function () {
  fetch('http://localhost:5000/read_xlsx_files_data', {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      input_files = data.data
      mode = data.mode
      input_file_paths = Object.keys(input_files)
      load_current_file_data()
    })
};

function load_current_file_data() {
  current_file_path = input_file_paths[current_file_index]
  current_file_info = input_files[current_file_path]

  display_filename(current_file_path)
  fill_column_layout(current_file_info)
}

function display_filename(file_path) {
  var file_name = file_path.split('\\').at(-1)
  const file_name_elem = document.getElementById('file_name');
  file_name_elem.innerText = file_name;
}

function fill_column_layout(file_info) {
  var multiple_address_parts = document.getElementById('multiple_address_parts')
  var is_multiple_address_parts = multiple_address_parts.checked
  radioContainer.innerHTML = ''
  file_info.columns.forEach((column, column_index) => {
    add_a_column_to_layout(column, column_index, file_info.type, is_multiple_address_parts)
  })
  all_radio_btns = form.querySelectorAll('input[type="radio"]');
}

function add_a_column_to_layout(column_name, column_index, column_type, is_multiple_address_parts) {
  const row_container_div = document.createElement('div');
  row_container_div.className = 'row';
  const column_name_span = document.createElement('span');
  column_name_span.className = 'col'
  column_name_span.textContent = column_name;
  row_container_div.appendChild(column_name_span);
  const radio_btns_container = document.createElement('div');
  radio_btns_container.className = 'col'
  input_color_mapping = {
    'First Name': 'bg-warning',
    'Last Name': 'bg-success',
    'Phone': 'bg-primary',
  }
  if (is_multiple_address_parts) {
    address_parts_color_mapping = {
      'Street Address': 'bg-secondary',
      'City': 'bg-info',
      'State': 'bg-dark',
      'Zipcode': 'bg-pink',
      'Unit': 'bg-wheat',
    }
  } else {
    address_parts_color_mapping = {
      'Address': 'bg-danger'
    }
    
  }
  input_color_mapping = { ...input_color_mapping, ...address_parts_color_mapping }
  dnc_color_mapping = {
    'Phone': {
      'Phone': 'bg-primary',
    },
    'Address': {
      'Address': 'bg-danger'
    }
  }
  if (column_type === 'input') {
    radio_colors = input_color_mapping
  } else if (column_type === 'dnc') {
    radio_colors = dnc_color_mapping[mode]
  }
  for (var key in radio_colors) {
    const radioInput = document.createElement('input');
    radioInput.type = 'radio';
    radioInput.id = `radio_${column_index}`;
    radioInput.className = `form-check-input m-2 ${radio_colors[key]}`;
    radioInput.name = `radio_${column_index}`;
    radioInput.value = key;
    radioInput.dataset.column = key;
    radio_btns_container.appendChild(radioInput);
  }
  row_container_div.appendChild(radio_btns_container);
  // from camelCase convert them to snake_case
  radioContainer.appendChild(row_container_div);
}

function load_next_file_if_exists() {
  if (is_valid_column_selection()) {
    current_file_index += 1;
    var selected_columns = get_selected_columns(current_file_info.columns)
    if (current_file_info.type === 'input') {
      selected_input_files_column_mapping[current_file_path] = selected_columns
    } else if (current_file_info.type === 'dnc') {
      selected_dnc_files_column_mapping[current_file_path] = selected_columns
    }
    if (current_file_index >= input_file_paths.length) {
      // test
      console.log(selected_input_files_column_mapping)
      pass_the_column_selection_to_server()
      // Check if any column is not selected show error
    } else {
      load_current_file_data()
    }
  } else {
    alert('Please select at least one option from each group.')
  }
}


function get_selected_columns(columns) {
  // Build the id of radio button
  var selected_columns = {}

  columns.forEach((column_name, column_index) => {
    selected_radio = document.querySelector(`#radio_${column_index}:checked`)
    if (selected_radio != null) {
      selected_columns[selected_radio.value] = column_name
    }
  })
  return selected_columns
}

function is_valid_column_selection() {
  const radio_groups = ['First Name', 'Last Name', 'Phone', 'Address', 'Street Address', 'City', 'State', 'Zipcode', 'Unit'];
  let is_valid = true;
  for (const group_name of radio_groups) {
    const radio_group = document.querySelectorAll(`input[data-column="${group_name}"][type="radio"]`);
    if (radio_group.length > 0) {
      const is_any_radio_selected = Array.from(radio_group).some(radio => radio.checked);
      is_valid = is_valid && is_any_radio_selected;
    }
  }
  return is_valid
}

function pass_the_column_selection_to_server() {
  fetch('http://localhost:5000/radio_button_selected_value', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: {
        'input_files': selected_input_files_column_mapping,
        'dnc_files': selected_dnc_files_column_mapping
      }
    }),
  })
    .then(response => response.json())
    .then(result => {
      console.log('Server response:', result);
      window.location = '../html/file-download.html'
    })
    .catch(error => {
      console.error('Error sending data to server:', error);
    });
}

var form = document.getElementById('radio-form');
function clear_selected_columns(selected_radio) {
  all_radio_btns.forEach(function (radio) {
    if (radio.dataset.column === selected_radio.dataset.column && radio.name !== selected_radio.name) {
      radio.checked = false;
    }
  });
}
form.addEventListener('change', function (e) {
  if (e.target.type === 'radio' && e.target.checked) {
    clear_selected_columns(e.target);
  }
});
