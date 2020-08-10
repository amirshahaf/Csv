import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import csv
from glob import glob
from shutil import copy
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Image upload parameters
MYDIR = os.path.dirname(__file__)
ALLOWED_EXTENSIONS = {'csv'}

# Flask parameters
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/files/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = '8a7f43415792dadc4d9e41fef6f45307'
upload_folder = MYDIR + "/" + app.config['UPLOAD_FOLDER']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def saving(files, directory):
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder + f'{directory}/', filename))
    return [file.name for file in files]


class FileMatch:

    def __init__(self, directory_a='a', directory_b='b', directory_c='c', minimal=90):
        # Directory A - files 2 be compared. (default = 'a'')

        self.directory_a = glob(upload_folder + directory_a + '/*.csv')

        # Directory B -Files 2 for comparing to. (default = 'b')
        self.directory_b = self.directory_loading(upload_folder + directory_b)

        # Directory C - matched files. (default = 'c')
        self.directory_c = upload_folder + directory_c

        self.scores = f'{self.directory_c}/scores.txt'

        # Minimal percentage for files to count as matched. (default = 90%)
        self.minimal = minimal

    # Loads all the files in directory b for comparing
    def directory_loading(self, directory):
        with ThreadPoolExecutor() as executor:
            pool = executor.map(self.file_load, glob(f'{directory}/*.csv'))
            return tuple(pool)

    def file_load(self, file):
        with open(file) as table:
            reader = csv.reader(table)
            return {line[0] for line in reader}

    def save(self, file, match_percent):
        copy(file, self.directory_c)
        with open(self.scores, "a") as scores:
            print(f"Name: {Path(file).name}  Match percent: {match_percent}%", file=scores)

    # Comparing a file with all the files in directory b
    def comparing(self, csv_file):
        with open(csv_file) as file:
            reader = csv.reader(file)
            origin = {line[0] for line in reader}
            for compared in self.directory_b:
                match_percent = (len(origin & compared) / float(len(origin | compared)) * 100)
                if match_percent > self.minimal:
                    return self.save(csv_file, match_percent)


@app.route('/', methods=['post', 'get'])
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        for folder in glob(upload_folder + '*/'):
            for file in glob(folder + '*'):
                os.remove(file)

        saving(request.files.getlist('directory_a[]'), 'a')
        saving(request.files.getlist('directory_b[]'), 'b')
        match = request.form['match']
        file_match = FileMatch(minimal=int(match))

        # Comparing files from directory A with files from directory B in parallel
        with ThreadPoolExecutor() as executor:
            future = executor.map(file_match.comparing, file_match.directory_a)

        try:
            with open(file_match.scores) as file:
                return jsonify({"success": True, "result": [line for line in file]})
        except FileNotFoundError:
            return jsonify({"success": False, "result": 'No matches found'})

