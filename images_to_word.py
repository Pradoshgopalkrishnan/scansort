from pathlib import Path
import docx

def create_word_from_images(image_folder: str, output_word_path: str):
    img_dir = Path(image_folder)
    
    # Safety check: does the image folder actually exist?
    if not img_dir.exists():
        raise FileNotFoundError(f"Image folder not found: {img_dir}")
        
    # 1. Create a blank Word document in memory
    doc = docx.Document()
    doc.add_heading("Extracted Images Report", level=0)  # level=0 makes it a Title
    
    # 2. Gather and sort the images
    # We only want to pick up actual image files, just in case other files are in there
    valid_extensions = {".png", ".jpg", ".jpeg"}
    images = [f for f in img_dir.iterdir() if f.suffix.lower() in valid_extensions]
    images.sort()  # Sorts them alphabetically so they appear in order
    
    if not images:
        print(f"No images found in '{img_dir.resolve()}'.")
        return
        
    print(f"[INFO] Found {len(images)} images. Building Word document...")
    
    # 3. Loop through the saved images
    for index, img_path in enumerate(images, start=1):
        
        # Add a heading for the image (e.g., "Figure 1: page_001_img_01_xref5.png")
        doc.add_heading(f"Figure {index}: {img_path.name}", level=1)
        
        # Insert the image into the document
        # Note: python-docx requires the path to be a standard string, not a Path object
        doc.add_picture(str(img_path))
        
        print(f"  -> Inserted Figure {index}: {img_path.name}")
        
    # 4. Save the finished document to your hard drive
    doc.save(output_word_path)
    print(f"\n[DONE] Successfully saved Word document to '{output_word_path}'")

if __name__ == "__main__":
    # Point to the folder where your previous script saved the images
    IMAGE_DIR = r"C:\Users\HP\PROJECTS\scansort\extracted_images"
    
    # Name the output Word file
    OUTPUT_DOCX = r"C:\Users\HP\PROJECTS\scansort\images_report.docx"
    
    create_word_from_images(IMAGE_DIR, OUTPUT_DOCX)