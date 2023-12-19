from flask import Flask, request, render_template, redirect, url_for
import PyPDF2
import re
import os
from werkzeug.utils import secure_filename
import magic

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Kontrollerar att katalogen för uppladdningar finns
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['GET', 'POST'])  # Updated to handle GET requests
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Spara filen temporärt
            file.save(file_path)
            # Kontrollera MIME-typen
            file_mime_type = magic.from_file(file_path, mime=True)
            if file_mime_type == 'application/pdf':
                try:
                    text = extract_text_from_pdf(file_path)
                    name, courses_list = clean_text(text)
                    gpa = calculate_gpa(courses_list)
                    # Choose background image based on GPA
                    background_image = choose_background_image(gpa)
                    # Radera filen efter att vi är klara
                    os.remove(file_path)
                    return render_template('gpa_result.html', name=name, courses=courses_list, gpa=gpa, background_image=background_image)
                except Exception as e:
                    os.remove(file_path)  # Se till att radera filen även vid fel
                    return str(e)
            else:
                os.remove(file_path)  # Radera filen om det inte är en PDF
                return "Ogiltig filtyp, endast PDF-filer är tillåtna."
        else:
            return "Ingen fil vald för uppladdning."
    else:
        # For GET requests, you can return the upload form or redirect to the home page
        return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def choose_background_image(gpa):
    if gpa >= 5:
        return 'gpa5.jpg'
    elif gpa >= 4.5:
        return 'gpa4.5.jpg'
    elif gpa >= 4.25:
        return 'gpa4.25.jpg'
    elif gpa >= 4:
        return 'gpa4.jpg'
    elif gpa >= 3.75:
        return 'gpa3.75.jpg'
    elif gpa >= 3.5:
        return 'gpa3.5.jpg'
    elif gpa > 3.0:
        return 'gpa3+.jpg'
    else:
        return 'gpa3.jpg'

# Funktion för att rensa texten och returnera en lista av kurser
def clean_text(text):
    # Extraherar namnet
    name_match = re.search(r'Namn Personnummer\s+([\w\s]+)\s+\d', text)
    name = name_match.group(1).strip() if name_match else "Namn ej hittat"

    # Extraherar kurser
    course_pattern = re.compile(r'^(.+) (\d{1,2},\dhp) ([ABCDE]) (\d{4}-\d{2}-\d{2}) 1$', re.MULTILINE)
    courses = course_pattern.findall(text)

    # Returnerar namn och kurslista
    return name, [list(course) for course in courses]


def calculate_gpa(courses_list):
    grade_points = {'A': 5, 'B': 4.5, 'C': 4, 'D': 3.5, 'E': 3}
    total_points = 0
    total_credits = 0

    for course in courses_list:
        course_name, hp_str, grade, date = course
        hp = float(hp_str.replace('hp', '').replace(',', '.'))
        points = grade_points.get(grade, 0) * hp
        total_points += points
        total_credits += hp

    # Rounding to the nearest two decimal places
    gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
    return gpa



#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))