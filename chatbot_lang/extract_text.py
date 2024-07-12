from PIL import Image

import pytesseract
# Open the image file
img_path = "449746215_1127289051684027_6135635112531640115_n.jpg"
img = Image.open(img_path)

# Use OCR to extract text from the image

# Perform OCR on the image
text = pytesseract.image_to_string(img)
print(text)
