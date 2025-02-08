import cv2
import pytesseract
import json
import psycopg2
from psycopg2.extras import Json
from pdf2image import convert_from_path
import os
import re
import numpy as np

# Configure Tesseract OCR Path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(image_path):
    """Preprocess image to enhance OCR accuracy."""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh


def extract_text_from_image(image_path):
    """Extract text using OCR."""
    preprocessed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(preprocessed_img, config='--psm 6',lang='eng')
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    text = re.sub(r'[_-]+', ' ', text)  # Remove unwanted underscores and dashes
    print("Extracted Text:\n", text)  # Debugging: Print extracted text
    return text


def extract_data(text):
    """Parse extracted text to identify key data points dynamically."""
    data = {}

    # Using flexible regex patterns to handle variations
    #data["patient_name"] = re.search(r'Patient Name[:\s]+([A-Za-z ]+)', text, re.IGNORECASE)
    data["patient_name"] = re.search(r'Patient Name[:\s]+([\w\s]+?)(?=\sDOB)', text, re.IGNORECASE)

    #data["dob"] = re.search(r'DOB[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})', text, re.IGNORECASE)
    data["dob"] = re.search(r'DOB[:\s]+([\d\s/-]+)', text, re.IGNORECASE)

    #data["date"] = re.search(r'Date[:\s]+([\d\s/-]+)', text, re.IGNORECASE)
    match = re.search(r'Date[:\s]+([\d\s/-]+)', text, re.IGNORECASE)
    data["date"] = match.group(1).strip() if match else "Unknown"

    data["injection"] = "Yes" if re.search(r'INJECTION[:\s]+YES', text, re.IGNORECASE) else "No"
    data["exercise_therapy"] = "Yes" if re.search(r'Exercise Therapy[:\s]+YES', text, re.IGNORECASE) else "No"

    # Convert regex matches to values safely
    for key in ["patient_name", "dob"]:
        match = data[key]
        data[key] = match.group(1).strip() if isinstance(match, re.Match) else "Unknown"

    # Extract pain symptoms
    pain_symptoms = {}
    symptoms = ["Pain", "Numbness", "Tingling", "Burning", "Tightness"]
    for symptom in symptoms:
        match = re.search(rf'{symptom}[:\s]+(\d+)', text, re.IGNORECASE)
        pain_symptoms[symptom.lower()] = int(match.group(1)) if match else None
    data["pain_symptoms"] = pain_symptoms

    # Extract Medical Assistant data
    medical_assistant_data = {}
    match = re.search(r'Blood Pressure[:\s]+(\d+/\d+)', text, re.IGNORECASE)
    medical_assistant_data["blood_pressure"] = match.group(1) if match else None
    match = re.search(r'HR[:\s]+(\d+)', text, re.IGNORECASE)
    medical_assistant_data["hr"] = int(match.group(1)) if match else None
    match = re.search(r'Weight[:\s]+(\d+)', text, re.IGNORECASE)
    medical_assistant_data["weight"] = int(match.group(1)) if match else None
    match = re.search(r'Height[:\s]+(\d+\s*\d*)', text, re.IGNORECASE)
    medical_assistant_data["height"] = match.group(1).replace(" ", "'") if match else None
    match = re.search(r'SpO2[:\s]+(\d+)', text, re.IGNORECASE)
    medical_assistant_data["spo2"] = int(match.group(1)) if match else None
    match = re.search(r'Temperature[:\s]+(\d+\.\d+)', text, re.IGNORECASE)
    medical_assistant_data["temperature"] = float(match.group(1)) if match else None
    match = re.search(r'Blood Glucose[:\s]+(\d+)', text, re.IGNORECASE)
    medical_assistant_data["blood_glucose"] = int(match.group(1)) if match else None
    match = re.search(r'Respirations[:\s]+(\d+)', text, re.IGNORECASE)
    medical_assistant_data["respirations"] = int(match.group(1)) if match else None

    data["medical_assistant_data"] = medical_assistant_data

    print("Extracted Data:\n", json.dumps(data, indent=4))  # Debugging: Print extracted data

    return json.dumps(data)


def save_to_database(data):
    """Save extracted data to PostgreSQL."""
    conn = psycopg2.connect(
        dbname="hospital_db", user="postgres", password="12345678", host="localhost", port="5432"
    )
    cursor = conn.cursor()

    parsed_data = json.loads(data)
    patient_name = parsed_data.get("patient_name", "Unknown")
    dob = parsed_data.get("dob", "0000-00-00")
    print(patient_name,dob)

    cursor.execute("""
        INSERT INTO patients (name, dob) VALUES (%s, %s) RETURNING id;
    """, (patient_name, dob))
    patient_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO forms_data (patient_id, form_json) VALUES (%s, %s);
    """, (patient_id, Json(parsed_data)))

    conn.commit()
    cursor.close()
    conn.close()


def process_document(file_path):
    """Process PDF or image file and store extracted data."""
    if file_path.lower().endswith(".pdf"):
        images = convert_from_path(file_path,poppler_path=r"D:\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin")
        for i, image in enumerate(images):
            temp_path = f"temp_page_{i}.jpg"
            image.save(temp_path, "JPEG")
            text = extract_text_from_image(temp_path)
            os.remove(temp_path)
    else:
        text = extract_text_from_image(file_path)

    extracted_data = extract_data(text)
    print('---------------------------'+'\n'+extracted_data)
    save_to_database(extracted_data)
    print("Data saved successfully!")


if __name__ == "__main__":
    process_document("sample2.pdf")