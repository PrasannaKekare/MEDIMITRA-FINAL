import os
import easyocr
import cv2
import requests
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(env_path, override=True)

# Configure NVIDIA API
NVIDIA_API_KEY = "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"
NVIDIA_INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Default prompt to instruct Gemini to extract medicine details
default_prompt = """
You are a medical assistant AI. You will be provided with text extracted from a prescription using OCR. 
Your job is to extract the following details from the text:
1. Medicine names
2. Dosage information (e.g., number of pills, mg, etc.)
3. Frequency (e.g., how many times per day)
4. Times (e.g., specific times to take the medicine)

Please provide the extracted information in a clear, structured format. If any details are missing, mention that they are not provided in the text.
"""

# Function to preprocess the image for OCR
def preprocess_image(image_path):
    # Load image using OpenCV
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding to binarize the image
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # Save preprocessed image (for debugging/testing)
    processed_image_path = 'processed_image.png'
    cv2.imwrite(processed_image_path, thresh)

    return processed_image_path

# Function to extract text using EasyOCR
def extract_text_from_image(image_path):
    reader = easyocr.Reader(['en'])  # Initialize EasyOCR reader for English
    processed_image_path = preprocess_image(image_path)
    result = reader.readtext(processed_image_path, detail=0)  # Extract text
    text = ' '.join(result)
    return text

# Function to send extracted text to Gemini for parsing
def parse_with_gemini(extracted_text):
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta/llama-3.2-11b-vision-instruct",
        "messages": [
            {
                "role": "user",
                "content": f"{default_prompt}\n\nPrescription Text:\n{extracted_text}"
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.3,
        "top_p": 1.00
    }
    
    response = requests.post(NVIDIA_INVOKE_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']

# Main OCR + Gemini parsing pipeline
def ocr_pipeline_with_gemini(image_path):
    # Step 1: Extract text from image using EasyOCR
    extracted_text = extract_text_from_image(image_path)
    print(f"\nExtracted Text:\n{extracted_text}")

    # Step 2: Send the extracted text to Gemini for parsing
    parsed_info = parse_with_gemini(extracted_text)
    print(f"\nParsed Prescription Information:\n{parsed_info}")

# Example usage
if __name__ == "__main__":
    # Replace with the path to your prescription image
    image_path = 'sample_prescription.png'
    
    # Run the OCR and parsing pipeline
    ocr_pipeline_with_gemini(image_path)
