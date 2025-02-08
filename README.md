# text_extraction_ocr

This project extracts data from patient assessment forms (images or PDFs) using Optical Character Recognition (OCR) and stores the extracted data into a PostgreSQL database.

Installation Instructions
Ensure you have Python 3.x installed on your system.

Install Required Modules
Run the following commands to install the necessary Python packages:
1. pip install opencv-python  # Open-CV for image processing
2. pip install pytesseract    # OCR processing
3. pip install psycopg2       # PostgreSQL database integration
4. pip install pdf2image      # Convert PDFs to images

Install and Configure Tesseract OCR
1. Download and install Tesseract OCR.
2. Add the installation path to your script. Default path for Windows:
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

Install Poppler for PDF Processing
1. Windows: Download Poppler from here and extract it.
2. Add the bin folder to your system PATH.
3. Update the script with the correct poppler_path:
   convert_from_path(file_path, poppler_path=r'D:\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin')
