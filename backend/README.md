# PrioritySort Backend

Python Flask backend with ML classification using SVM and Naive Bayes.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

3. Install Poppler (for PDF support):
- **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases/
- **Mac**: `brew install poppler`
- **Linux**: `sudo apt-get install poppler-utils`

4. Create `.env` file with Gmail credentials:
```
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

5. Run the server:
```bash
python app.py
```

Server will run on http://localhost:5000

## API Endpoints

- `POST /api/upload` - Upload and classify petitions
- `GET /api/petitions` - Get all petitions
- `POST /api/send-email/<id>` - Send petition via email
- `GET /api/statistics` - Get statistics

## ML Models

- **SVM (Support Vector Machine)**: Department classification
- **Naive Bayes**: Priority classification
- Models are trained on initialization with sample data
