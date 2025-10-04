import requests
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import json

def create_high_quality_bill():
    """Create a high-quality, OCR-friendly medical bill"""
    # Larger, higher quality image
    img = Image.new('RGB', (1200, 1600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use larger, clearer fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        text_font = ImageFont.truetype("arial.ttf", 45)
        bold_font = ImageFont.truetype("arialbd.ttf", 50)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
    
    # Header with high contrast
    draw.rectangle([(0, 0), (1200, 150)], fill='#1976D2')
    draw.text((300, 45), "CITY HOSPITAL", fill='white', font=title_font)
    
    # Bill content with clear spacing and high contrast
    y = 220
    lines = [
        ("MEDICAL INVOICE", bold_font, 'black'),
        ("Invoice No: 2024-001", text_font, 'black'),
        ("Date: 15-Jan-2024", text_font, 'black'),
        ("", text_font, 'black'),
        ("Services:", bold_font, 'black'),
        ("", text_font, 'black'),
        ("Doctor Consultation Fee    Rs 500", text_font, 'black'),
        ("Medicines Cost            INR 800", text_font, 'black'),
        ("Blood Test                Rs 600", text_font, 'black'),
        ("X-Ray Charges            INR 900", text_font, 'black'),
        ("", text_font, 'black'),
        ("", text_font, 'black'),
        ("Subtotal                 Rs 2800", text_font, 'black'),
        ("Tax 5%                   Rs 140", text_font, 'black'),
        ("", text_font, 'black'),
        ("Total Amount             Rs 2940", bold_font, 'red'),
        ("Amount Paid              Rs 2000", text_font, 'green'),
        ("Balance Due              Rs 940", bold_font, 'red'),
    ]
    
    for line, font, color in lines:
        draw.text((100, y), line, fill=color, font=font)
        y += 60
    
    # Footer
    draw.text((350, 1450), "Thank You!", fill='gray', font=text_font)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG', quality=95, dpi=(300, 300))
    img_bytes.seek(0)
    
    return img_bytes.read()

# Create the bill
print("Creating high-quality medical bill image...")
image_data = create_high_quality_bill()

# Save to file
with open('high_quality_bill.png', 'wb') as f:
    f.write(image_data)
print("✅ Bill image saved as: high_quality_bill.png")
print("   (You can open this file to see what was generated)")

# Encode to base64
encoded_image = base64.b64encode(image_data).decode('utf-8')

# Test the API
print("\n" + "="*60)
print("Testing API with Image OCR...")
print("="*60)

url = 'http://localhost:5000/api/extract/complete'

try:
    response = requests.post(url, json={'image': encoded_image})
    
    print(f"\nStatus Code: {response.status_code}")
    print("\nAPI Response:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("Testing API with Plain Text (for comparison)...")
print("="*60)

# Also test with plain text to compare
text_payload = {
    "text": """
    MEDICAL INVOICE
    Invoice No: 2024-001
    
    Doctor Consultation Fee: Rs 500
    Medicines Cost: INR 800
    Blood Test: Rs 600
    X-Ray Charges: INR 900
    
    Subtotal: Rs 2800
    Tax 5%: Rs 140
    
    Total Amount: Rs 2940
    Amount Paid: Rs 2000
    Balance Due: Rs 940
    """
}

try:
    response2 = requests.post(url, json=text_payload)
    print(f"\nStatus Code: {response2.status_code}")
    print("\nAPI Response:")
    print(json.dumps(response2.json(), indent=2))
    
except Exception as e:
    print(f"❌ Error: {e}")