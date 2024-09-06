from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from ListStacker import ListStacker
import pandas as pd
import glob
import os
import signal
import sys
app = Flask(__name__)

UPLOAD_FOLDER = os.path.abspath('uploads')
DNC_UPLOAD_FOLDER = os.path.abspath('uploads_dnc_files')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DNC_UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DNC_UPLOAD_FOLDER'] = DNC_UPLOAD_FOLDER

list_stacker = ListStacker()


def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, '*'))
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error deleting file {file}: {str(e)}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    file_columns = {}
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        delete_files_in_folder(UPLOAD_FOLDER)
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
        excel_files = glob.glob(os.path.join(UPLOAD_FOLDER, '*.xlsx'))
        for file in excel_files:
            file = os.path.abspath(file)
            df = pd.read_excel(file)
            file_columns[file] = list(df.columns)
            # TODO: Read headers data efficiently
        dic = {'fileName': [], 'list_data': []}
        for key, value in file_columns.items():
            dic['fileName'].append(key)
            dic['list_data'].append(value)
        return jsonify({'message': 'Files uploaded successfully', 'data': dic})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/send_keyword_list_data', methods=['POST'])
def send_keyword_list_data():
    keyword_list = request.json.get('keywordList', None)
    mode = request.json.get('mode', False)
    keyword_filter = request.json.get('keyword', False)
    extract_duplicates = request.json.get('extractDuplicates', False)
    remove_dnc_bool = request.json.get('removeDNCRecords', False)
    combine_all_list_bool = request.json.get('combineAllLists', False)
    remove_old_processed_records = request.json.get(
        'removeOldProcessedRecords', False)

    if mode == True:
        mode = "Phone"
    else:
        mode = "Address"

    if keyword_list is not None:
        list_stacker.set_settings(
            mode=mode,
            keyword_filter=keyword_filter,
            keyword_list=keyword_list,
            is_to_extract_duplicates=extract_duplicates,
            remove_dnc_bool=remove_dnc_bool,
            combine_all_list_bool=combine_all_list_bool,
            remove_old_processed_records=remove_old_processed_records
        )
        settings = {
            "mode": mode,
            'keyword_filter': keyword_filter,
            'keyword_list': keyword_list
        }
        return jsonify({'message': 'Data received keyword data successfully', "toggle": settings})
    else:
        return jsonify({'error': 'No data received'})


@app.route('/read_xlsx_files_data', methods=['GET'])
def read_xlsx_files_data():
    files_data = {}

    folder_type_dict = {
        app.config['UPLOAD_FOLDER']: 'input',
        app.config['DNC_UPLOAD_FOLDER']: 'dnc'
    }
    try:
        for folder, file_type in folder_type_dict.items():
            excel_files = glob.glob(folder + '/*.xlsx')
            for file in excel_files:
                file = os.path.abspath(file)
                df = pd.read_excel(file)
                file_info = {}
                file_info['type'] = file_type
                file_info['columns'] = list(df.columns)

                files_data[file] = file_info
        return jsonify({'message': 'Files uploaded successfully', 'data': files_data, 'mode': list_stacker.mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def allowed_dnc_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_dnc_files', methods=['POST'])
def upload_dnc_files():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        upload_folder = app.config['DNC_UPLOAD_FOLDER']
        delete_files_in_folder(upload_folder)
        file.save(os.path.join(upload_folder, file.filename))
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/radio_button_selected_value', methods=['POST'])
def radio_button_selected_value():
    file_column_mapping = request.json.get('data', None)
    if file_column_mapping is not None:
        list_stacker.main(file_column_mapping, app.config['UPLOAD_FOLDER'])
        return jsonify({'message': 'Received radio button data successfully'})


@app.route('/saveToFolder', methods=['POST'])
def getOutputFolder():
    output_folder_path = request.json.get('output_folder_path', None)
    # output_folder_path = os.path.realpath(output_folder_path)
    try:
        list_stacker.save_output_files(output_folder_path)
        return jsonify({'status': 'success', 'message': f'Successfully saved files to the path: {output_folder_path}', 'output_folder_path':output_folder_path})
    except FileExistsError as e:
        return jsonify({'status': 'error', 'message': f'File already exists at path: {str(e)}'})


def signal_handler(sig, frame):
    sys.exit(0)  # or you can raise an exception like: raise SystemExit()


if __name__ == '__main__':

    # Deleting any file in DNC folder as we made DNC File optional so
    # to make sure we don't use any used dnc file
    upload_folder = app.config['DNC_UPLOAD_FOLDER']
    delete_files_in_folder(upload_folder)


    from waitress import serve
    bind_address = '127.0.0.1'
    port = 5000

    signal.signal(signal.SIGINT, signal_handler)
    serve(app, host=bind_address, port=port)
