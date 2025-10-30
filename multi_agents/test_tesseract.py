import pytesseract
from PIL import Image
import sys

def test_tesseract():
    print(f"Python version: {sys.version}")
    print(f"\nTesseract version: {pytesseract.get_tesseract_version()}")
    print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

if __name__ == "__main__":
    test_tesseract()