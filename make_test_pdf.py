import pymupdf

def create_test_pdf():
    # 1. Create a blank PDF
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    
    # 2. Add some text
    page.insert_text((50, 50), "Digital PDF Embedded Image Test", fontsize=16)

    # 3. Create a raw orange image in memory
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 150, 150), False)
    pix.set_rect(pix.irect, (255, 100, 50))  # Solid orange block
    image_bytes = pix.tobytes("png")

    # 4. Embed the image into the page
    # Rect(x0, y0, x1, y1) controls where the image goes
    rect = pymupdf.Rect(50, 100, 200, 250)
    page.insert_image(rect, stream=image_bytes)

    # 5. Save the PDF
    filename = "test_sample.pdf"
    doc.save(filename)
    doc.close()
    
    print(f"[SUCCESS] Created {filename} directly. No Word export needed.")

if __name__ == "__main__":
    create_test_pdf()