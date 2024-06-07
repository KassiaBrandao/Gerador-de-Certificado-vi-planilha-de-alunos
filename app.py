from flask import Flask, render_template, request, send_file, after_this_request
from PIL import Image, ImageDraw, ImageFont
import openpyxl
import os
import sys
import shutil
import zipfile

app = Flask(__name__)

def resource_path(relative_path):
    """ Obter o caminho absoluto para o recurso, funcionando para o PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado', 400
    file = request.files['file']
    if file.filename == '':
        return 'Nenhum arquivo selecionado', 400
    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        zip_path = generate_certificates(file_path)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(zip_path)
                shutil.rmtree(resource_path('certificados'))
            except Exception as error:
                app.logger.error("Erro ao tentar remover arquivos temporários", error)
            return response

        return send_file(zip_path, as_attachment=True)

def generate_certificates(file_path):
    workbook_students = openpyxl.load_workbook(file_path)
    sheet_students = workbook_students['Sheet2']

    output_dir = resource_path('certificados')
    os.makedirs(output_dir, exist_ok=True)

    output_paths = []

    for indice, line in enumerate(sheet_students.iter_rows(min_row=2, max_row=10)):
        student_name = line[0].value
        start_date = line[1].value
        end_date = line[2].value
        student_name = student_name.title()

        font_name = ImageFont.truetype(resource_path('static/GreatVibes-Regular.ttf'), 90)
        font_text = ImageFont.truetype(resource_path('static/Montserrat-Regular.ttf'), 30)

        image = Image.open(resource_path('static/certificado_geo.jpg'))
        draw = ImageDraw.Draw(image)

        bbox = draw.textbbox((0, 0), student_name, font=font_name)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        image_width, image_height = image.size

        x_name = (image_width - text_width) / 2
        y_name = 435

        x_date = 340
        y_start_date = 852
        y_end_date = 895

        draw.text((x_name, y_name), student_name, fill='#a69464', font=font_name)
        draw.text((x_date, y_start_date), start_date, fill='#fff', font=font_text)
        draw.text((x_date, y_end_date), end_date, fill='#eaeaea', font=font_text)

        output_path = os.path.join(output_dir, f'certificado_{indice}_{student_name}.png')
        image.save(output_path)
        output_paths.append(output_path)

    # Criar um arquivo zip com todos os certificados
    zip_filename = resource_path('certificados.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in output_paths:
            zipf.write(file, os.path.basename(file))

    return zip_filename

if __name__ == '__main__':
    app.run(debug=True)