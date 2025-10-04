import base64

# Read the image
with open('high_quality_bill.png', 'rb') as image_file:
    encoded = base64.b64encode(image_file.read()).decode('utf-8')
    
# Save to file
with open('encoded_image.txt', 'w') as f:
    f.write(encoded)
    
print("Image encoded! Check encoded_image.txt")
print(f"Encoded length: {len(encoded)} characters")