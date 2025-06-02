from flask import Flask, render_template, request, redirect
from pytesseract import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import re
import cv2
import torch
import easyocr

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = torch.hub.load('ultralytics/yolov5', 'custom', path='weights/best.pt', force_reload=True)

reader = easyocr.Reader(['en'], gpu=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return redirect(request.url)
    file = request.files['image']
    if file.filename == '':
        return redirect(request.url)
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    plate_text = detect_and_read_plate(file_path)

    return render_template('index.html', plate_text=plate_text, image_path=file_path)

def detect_and_read_plate(image_path):
    img = cv2.imread(image_path)
    results = model(img)
    detections = results.xyxy[0]

    if len(detections) == 0:
        return "License Plate Not Detected"

    x1, y1, x2, y2 = map(int, detections[0][:4])
    plate_img = img[y1:y2, x1:x2]

    plate_pil = Image.fromarray(cv2.cvtColor(plate_img, cv2.COLOR_BGR2RGB))
    plate_pil = plate_pil.convert('L')
    plate_pil = ImageEnhance.Contrast(plate_pil).enhance(2)
    plate_pil = plate_pil.filter(ImageFilter.SHARPEN)

    debug_ocr_input_path = image_path.replace(".jpg", "_ocr_input.jpg")
    plate_pil.save(debug_ocr_input_path)

    img = Image.open(image_path)
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    text = pytesseract.image_to_string(img)
    print('aaaaaaaaaaaaaaaaaaaaa', text)

    return 'testtttt'

def extract_albanian_plate(raw_text):
    cleaned = raw_text.upper()
    cleaned = re.sub(r'[^A-Z0-9 ]+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    plate_pattern = r'\b[A-Z]{1,2}\s?\d{3,4}\s?[A-Z]{2}\b'
    matches = re.findall(plate_pattern, cleaned)

    if matches:
        return matches[0]
    else:
        no_space = cleaned.replace(' ', '')
        fallback_pattern = r'[A-Z]{2}\d{3,4}[A-Z]{2}'
        fallback_matches = re.findall(fallback_pattern, no_space)
        return fallback_matches[0] if fallback_matches else "License Plate Not Detected"

if __name__ == '__main__':
    app.run(debug=True)
