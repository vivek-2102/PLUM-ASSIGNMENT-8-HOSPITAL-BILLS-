from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import re
import io
import base64
from typing import Dict, List, Tuple
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Configure Tesseract path for Windows (update if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Gemini client
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    print("ERROR: GEMINI_API_KEY not set!")
    print("Please set it with: set GEMINI_API_KEY=your-key")
else:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-pro')
    print("✅ Gemini AI initialized successfully")

class AmountDetectionService:
    """Service for detecting and classifying amounts in medical documents"""
    
    def __init__(self):
        self.currency_patterns = {
            'INR': r'(?:INR|Rs\.?|₹)',
            'USD': r'(?:USD|\$)',
            'EUR': r'(?:EUR|€)',
        }
        
    def extract_text_from_image(self, image_data: bytes) -> Tuple[str, float]:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image)
            # Simple confidence based on text length and clarity
            confidence = min(0.95, len(text.strip()) / 100)
            return text, max(0.5, confidence)
        except Exception as e:
            raise Exception(f"OCR failed: {str(e)}")
    
    def step1_ocr_extraction(self, text: str = None, image_data: bytes = None) -> Dict:
        """Step 1: Extract raw tokens from text or image"""
        
        if image_data:
            text, ocr_confidence = self.extract_text_from_image(image_data)
        else:
            ocr_confidence = 0.95
        
        if not text or len(text.strip()) < 5:
            return {
                "status": "no_amounts_found",
                "reason": "document too noisy"
            }
        
        # Extract numeric tokens (including OCR errors like 'l' for '1', 'O' for '0')
        raw_tokens = []
        
        # Pattern for amounts with possible OCR errors
        patterns = [
            r'\d+(?:\.\d+)?%?',  # Normal numbers with optional % or decimals
            r'[lI]\d+',  # 'l' or 'I' followed by digits
            r'\d+[lI]',  # digits followed by 'l' or 'I'
            r'[Oo]\d+',  # 'O' or 'o' followed by digits
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            raw_tokens.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        raw_tokens = [x for x in raw_tokens if not (x in seen or seen.add(x))]
        
        if not raw_tokens:
            return {
                "status": "no_amounts_found",
                "reason": "no numeric values detected"
            }
        
        # Detect currency
        currency_hint = "INR"  # Default
        for curr, pattern in self.currency_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                currency_hint = curr
                break
        
        return {
            "raw_tokens": raw_tokens,
            "currency_hint": currency_hint,
            "confidence": round(ocr_confidence, 2)
        }
    
    def step2_normalization(self, raw_tokens: List[str]) -> Dict:
        """Step 2: Fix OCR errors and normalize to numbers"""
        
        normalized_amounts = []
        
        for token in raw_tokens:
            # Skip percentage values for now
            if '%' in token:
                continue
            
            # Fix common OCR errors
            cleaned = token.replace('l', '1').replace('I', '1')
            cleaned = cleaned.replace('O', '0').replace('o', '0')
            cleaned = cleaned.replace(',', '')
            
            try:
                amount = float(cleaned)
                if amount > 0:
                    # Convert to int if it's a whole number
                    normalized_amounts.append(int(amount) if amount.is_integer() else amount)
            except ValueError:
                continue
        
        confidence = 0.82 if normalized_amounts else 0.0
        
        return {
            "normalized_amounts": normalized_amounts,
            "normalization_confidence": confidence
        }
    
    def step3_classification(self, text: str, normalized_amounts: List[float]) -> Dict:
        """Step 3: Use Gemini AI to classify amounts by context"""
        
        if not normalized_amounts:
            return {
                "amounts": [],
                "confidence": 0.0
            }
        
        prompt = f"""Analyze this medical bill/receipt text and classify the amounts by their context.

Text: {text}

Amounts found: {normalized_amounts}

Common medical bill categories:
- total_bill: The total amount of the bill
- paid: Amount already paid
- due: Amount still due/outstanding
- discount: Discount amount
- consultation_fee: Doctor consultation fee
- medicine_cost: Cost of medicines
- test_cost: Cost of tests/procedures
- other: Other charges

For each amount, identify its type based on the surrounding text context.

Return ONLY a valid JSON object in this exact format:
{{
  "amounts": [
    {{"type": "category_name", "value": amount_number}},
    ...
  ],
  "confidence": 0.XX
}}"""

        try:
            response = gemini_model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                import json
                result = json.loads(json_match.group())
                return result
            else:
                return self._fallback_classification(text, normalized_amounts)
                
        except Exception as e:
            print(f"Gemini classification error: {e}")
            return self._fallback_classification(text, normalized_amounts)
    
    def _fallback_classification(self, text: str, amounts: List[float]) -> Dict:
        """Fallback rule-based classification"""
        text_lower = text.lower()
        classified = []
        
        keywords = {
            'total_bill': ['total', 'grand total', 'amount', 'bill'],
            'paid': ['paid', 'payment', 'received'],
            'due': ['due', 'balance', 'outstanding', 'pending'],
            'discount': ['discount', 'off'],
            'consultation_fee': ['consultation', 'doctor', 'visit'],
            'medicine_cost': ['medicine', '药', 'drugs', 'pharmacy'],
            'test_cost': ['test', 'lab', 'x-ray', 'scan'],
        }
        
        for amount in amounts:
            amount_str = str(int(amount))
            matched = False
            
            # Find context around the amount
            for category, terms in keywords.items():
                for term in terms:
                    pattern = f"{term}.*?{amount_str}|{amount_str}.*?{term}"
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        classified.append({"type": category, "value": amount})
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                classified.append({"type": "other", "value": amount})
        
        return {
            "amounts": classified,
            "confidence": 0.70
        }
    
    def step4_final_output(self, text: str, currency: str, classified_amounts: List[Dict]) -> Dict:
        """Step 4: Generate final output with provenance"""
        
        final_amounts = []
        
        for item in classified_amounts:
            amount_value = item['value']
            amount_str = str(int(amount_value))
            
            # Find source context in original text
            lines = text.split('\n')
            source = "unknown"
            
            for line in lines:
                if amount_str in line:
                    source = f"text: '{line.strip()[:50]}'"
                    break
            
            final_amounts.append({
                "type": item['type'],
                "value": amount_value,
                "source": source
            })
        
        return {
            "currency": currency,
            "amounts": final_amounts,
            "status": "ok"
        }
    
    def process_document(self, text: str = None, image_data: bytes = None) -> Dict:
        """Complete pipeline for processing a document"""
        
        # Step 1: OCR/Extraction
        step1_result = self.step1_ocr_extraction(text, image_data)
        if step1_result.get('status') == 'no_amounts_found':
            return step1_result
        
        # Step 2: Normalization
        step2_result = self.step2_normalization(step1_result['raw_tokens'])
        
        # Get text for further processing
        if image_data and not text:
            text, _ = self.extract_text_from_image(image_data)
        
        # Step 3: Classification with Gemini
        step3_result = self.step3_classification(text, step2_result['normalized_amounts'])
        
        # Step 4: Final Output
        final_result = self.step4_final_output(
            text,
            step1_result['currency_hint'],
            step3_result['amounts']
        )
        
        # Add confidence score
        final_result['confidence_score'] = step3_result.get('confidence', 0.75)
        
        return final_result


# Initialize service
service = AmountDetectionService()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "medical-amount-detection", "ai_model": "Gemini Pro"})


@app.route('/api/extract/step1', methods=['POST'])
def extract_step1():
    """Step 1: OCR/Text Extraction"""
    try:
        data = request.get_json()
        text = data.get('text')
        image_base64 = data.get('image')
        
        image_data = None
        if image_base64:
            image_data = base64.b64decode(image_base64)
        
        result = service.step1_ocr_extraction(text, image_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/extract/step2', methods=['POST'])
def extract_step2():
    """Step 2: Normalization"""
    try:
        data = request.get_json()
        raw_tokens = data.get('raw_tokens', [])
        
        result = service.step2_normalization(raw_tokens)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/extract/step3', methods=['POST'])
def extract_step3():
    """Step 3: Classification"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        normalized_amounts = data.get('normalized_amounts', [])
        
        result = service.step3_classification(text, normalized_amounts)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/extract/complete', methods=['POST'])
def extract_complete():
    """Complete pipeline - all steps"""
    try:
        data = request.get_json()
        text = data.get('text')
        image_base64 = data.get('image')
        
        image_data = None
        if image_base64:
            image_data = base64.b64decode(image_base64)
        
        result = service.process_document(text, image_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 Medical Amount Detection API - Gemini Edition")
    print("="*60)
    print("AI Model: Google Gemini Pro")
    print("Server starting on http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)