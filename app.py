import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from PIL import Image
import pytesseract
import google.generativeai as genai


genai.configure(api_key="YOUR_GEMINI_API_KEY") 
model = genai.GenerativeModel('gemini-pro')


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads' 
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def extract_text_from_image(image_path):
    """
    Uses Tesseract OCR to extract text from an image.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        return None

def process_with_gemini(invoice_text):
    """
    Sends the extracted text to Gemini API to get structured data.
    """
    if not invoice_text:
        return "No text extracted from invoice."

    prompt = f"""
    Extract the following information from the invoice text below. 
    If a piece of information is not found, output "N/A".

    Invoice Text:
    ---
    {invoice_text}
    ---

    Extract:
    Invoice Number:
    Date:
    Total Amount:
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Error processing with AI. Please try again."

# --- Flask Routes ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'invoice_image' not in request.files:
        return redirect(request.url)
    
    file = request.files['invoice_image']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 1. OCR Preprocessing
        extracted_text = extract_text_from_image(filepath)
        
        # 2. LLM Processing
        extracted_data = process_with_gemini(extracted_text)

    
        return render_template('results.html', 
                               invoice_image_filename=file.filename, 
                               extracted_text=extracted_text,
                               extracted_data=extracted_data)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)