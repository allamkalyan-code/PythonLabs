# Nutrition Label Analysis System

This application uses multiple AI agents to analyze nutrition labels from images and provide easy-to-understand explanations.

## Requirements

### 1. Python Environment
- Python 3.8 or higher
- Virtual environment (already set up)

### 2. Tesseract OCR Installation

#### Windows:
1. Download the Tesseract installer from the official UB Mannheim repository:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest installer (e.g., tesseract-ocr-w64-setup-v5.3.1.20230401.exe)

2. Run the installer:
   - Select your installation directory (default: `C:\Program Files\Tesseract-OCR`)
   - **Important**: Check the option to "Add to PATH" during installation
   - Complete the installation

3. Set environment variable:
   - If Tesseract is installed in a different location, add `TESSERACT_PATH` to your environment variables:
     - System Settings > Advanced System Settings > Environment Variables
     - Add new variable: `TESSERACT_PATH` with value: `C:\Program Files\Tesseract-OCR\tesseract.exe`
     - Update `PATH` to include: `C:\Program Files\Tesseract-OCR`

#### Linux:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### MacOS:
```bash
brew install tesseract
```

### 3. OpenAI API Key
1. Create a `.env` file in the project root
2. Add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Activate the virtual environment:
```bash
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/MacOS
```

2. Run the Streamlit app:
```bash
streamlit run src/app.py
```

3. Open your browser and go to:
   - Local URL: http://localhost:8501