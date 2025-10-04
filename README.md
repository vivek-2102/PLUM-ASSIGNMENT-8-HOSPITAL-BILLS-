# AI-Powered Medical Document Amount Detection API

A Flask-based REST API that extracts, normalizes, and classifies financial amounts from medical bills and receipts using OCR and AI.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Flask API Server            │
│  ┌───────────────────────────────┐  │
│  │  AmountDetectionService       │  │
│  │                               │  │
│  │  Step 1: OCR/Extraction       │  │
│  │  ├─ Tesseract OCR             │  │
│  │  └─ Token Extraction          │  │
│  │                               │  │
│  │  Step 2: Normalization        │  │
│  │  ├─ OCR Error Correction      │  │
│  │  └─ Number Conversion         │  │
│  │                               │  │
│  │  Step 3: Classification       │  │         
│  │  ├─ Gemini AI (Comparison)    │  │
│  │                               │  │
│  │  Step 4: Final Output         │  │
│  │  ├─ Confidence Scoring        │  │
│  │  └─ Provenance Tracking       │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

##  Setup Instructions

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR** - Install based on your OS:
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   ```
   
   **macOS:**
   ```bash
   brew install tesseract
   ```
   
   **Windows:**
   Download from: https://github.com/UB-Mannheim/tesseract/wiki

3. **Anthropic API Key** - Get from: https://console.anthropic.com/
4. **Google Gemini API Key** - Get from: https://makersuite.google.com/app/apikey

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd medical-amount-detection
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   export GEMINI_API_KEY='your-gemini-api-key-here'
   # On Windows: 
   # set GEMINI_API_KEY=your-gemini-api-key-here
   ```

5. **Run the server:**
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`

### Using ngrok (for external access)

```bash
# Install ngrok
# Download from: https://ngrok.com/download

# Start ngrok tunnel
ngrok http 5000
```

## 📡 API Endpoints

### 1. Health Check
```bash
GET /health
```

### 2. Step 1 - OCR/Extraction
```bash
POST /api/extract/step1
```

### 3. Step 2 - Normalization
```bash
POST /api/extract/step2
```

### 4. Step 3 - Classification
```bash
POST /api/extract/step3
```

### 5. Complete Pipeline
```bash
POST /api/extract/complete
```

## 🧪 Testing with cURL

### Test with Text Input

```bash
curl -X POST http://localhost:5000/api/extract/complete \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"
  }'
```

**Expected Response:**
```json
{
  "currency": "INR",
  "amounts": [
    {
      "type": "total_bill",
      "value": 1200,
      "source": "text: 'Total: INR 1200 | Paid: 1000 | Due: 200 | Disco'"
    },
    {
      "type": "paid",
      "value": 1000,
      "source": "text: 'Total: INR 1200 | Paid: 1000 | Due: 200 | Disco'"
    },
    {
      "type": "due",
      "value": 200,
      "source": "text: 'Total: INR 1200 | Paid: 1000 | Due: 200 | Disco'"
    }
  ],
  "status": "ok"
}
```

### Test with Gemini Comparison

```bash
curl -X POST http://localhost:5000/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Total: INR 1200 | Paid: 1000 | Due: 200"
  }'
```

**Expected Response:**
```json
{
  "currency": "INR",
  "amounts": [...],
  "status": "ok",
  "comparison": {
    "claude_classification": [...],
    "gemini_classification": [...],
    "agreement_analysis": {
      "agreement_score": 0.85,
      "matched_amounts": 3,
      "total_amounts": 3,
      "final_confidence": 0.82,
      "matches": [...],
      "mismatches": []
    },
    "final_confidence": 0.82
  },
  "confidence_score": 0.82
}
```

### Test Step 1 (OCR) Only

```bash
curl -X POST http://localhost:5000/api/extract/step1 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "T0tal: Rs l200 | Pald: 1000 | Due: 200"
  }'
```

**Expected Response:**
```json
{
  "raw_tokens": ["0", "200", "1000", "200"],
  "currency_hint": "INR",
  "confidence": 0.95
}
```

### Test Step 2 (Normalization)

```bash
curl -X POST http://localhost:5000/api/extract/step2 \
  -H "Content-Type: application/json" \
  -d '{
    "raw_tokens": ["l200", "1000", "200", "10%"]
  }'
```

**Expected Response:**
```json
{
  "normalized_amounts": [1200, 1000, 200],
  "normalization_confidence": 0.82
}
```

### Test Step 3 (Classification)

```bash
curl -X POST http://localhost:5000/api/extract/step3 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Total: INR 1200 | Paid: 1000 | Due: 200",
    "normalized_amounts": [1200, 1000, 200]
  }'
```

### Test with Image (Base64)

```bash
# First, encode your image to base64
base64 -i medical_bill.jpg -o encoded.txt

# Then send the request
curl -X POST http://localhost:5000/api/extract/complete \
  -H "Content-Type: application/json" \
  -d '{
    "image": "'"$(cat encoded.txt)"'"
  }'
```

### Test Error Handling (No Amounts)

```bash
curl -X POST http://localhost:5000/api/extract/complete \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This document has no numbers"
  }'
```

**Expected Response:**
```json
{
  "status": "no_amounts_found",
  "reason": "no numeric values detected"
}
```

##  Postman Collection

Import this JSON into Postman:

```json
{
  "info": {
    "name": "Medical Amount Detection API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:5000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["health"]
        }
      }
    },
    {
      "name": "Complete Pipeline - Text",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"text\": \"Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%\"\n}"
        },
        "url": {
          "raw": "http://localhost:5000/api/extract/complete",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["api", "extract", "complete"]
        }
      }
    },
    {
      "name": "Step 1 - OCR",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"text\": \"T0tal: Rs l200 | Pald: 1000 | Due: 200\"\n}"
        },
        "url": {
          "raw": "http://localhost:5000/api/extract/step1",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["api", "extract", "step1"]
        }
      }
    }
  ]
}
```

##  Features

✅ **Multi-format Support**: Text and image inputs  
✅ **OCR Integration**: Tesseract for image text extraction  
✅ **Error Correction**: Handles common OCR mistakes (l→1, O→0)  
✅ **Dual AI Classification**: Claude AI (primary) + Gemini AI (comparison)  
✅ **Confidence Scoring**: Agreement-based confidence calculation  
✅ **Model Comparison**: Side-by-side Claude vs Gemini results  
✅ **Fallback Logic**: Rule-based classification when AI unavailable  
✅ **Guardrails**: Proper error handling and validation  
✅ **Provenance Tracking**: Source attribution for each amount  
✅ **Multi-currency**: Supports INR, USD, EUR detection  

##  Error Handling

The API includes comprehensive error handling:

- **No amounts found**: Returns proper status when document is empty
- **OCR failures**: Graceful degradation with error messages
- **AI service errors**: Automatic fallback to rule-based classification
- **Invalid inputs**: Clear validation error messages

## 🛠️ Key Implementation Details

### OCR Error Correction
- Converts common misreads: `l`→`1`, `I`→`1`, `O`→`0`, `o`→`0`
- Handles partial visibility and crumpled documents

### AI Chaining
- Uses Claude Sonnet 4 for primary classification
- Uses Gemini Pro for comparison and validation
- Calculates confidence based on model agreement
- Provides examples to guide proper categorization
- Falls back to regex-based rules if AI unavailable

### Confidence Calculation
- Agreement score based on matching predictions
- Final confidence = average AI confidence × agreement factor
- Provides detailed match/mismatch analysis

### Amount Types Supported
- `total_bill`: Total amount
- `paid`: Paid amount
- `due`: Outstanding/due amount  
- `discount`: Discount amount
- `consultation_fee`: Doctor fees
- `medicine_cost`: Medicine charges
- `test_cost`: Lab test charges
- `other`: Miscellaneous charges

 

 

 