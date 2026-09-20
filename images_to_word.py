from pathlib import Path
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH


def build_word_doc(image_paths, output_word_path: str, images_per_page: int = 2):
    """
    Builds the Word doc from an explicit list of image paths.
    Each image is sized to the full page width and centered, with a page
    break inserted after every `images_per_page` images, so you get exactly
    that many large images per page instead of a small-thumbnail grid.
    No title, no "Figure N" headings — just the images.
    """
    doc = docx.Document()

    image_paths = [Path(p) for p in image_paths]
    if not image_paths:
        print("No images to add.")
        return

    print(f"[INFO] Building Word document from {len(image_paths)} image(s)...")

    section = doc.sections[0]
    usable_width = section.page_width - section.left_margin - section.right_margin

    for index, img_path in enumerate(image_paths):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(str(img_path), width=usable_width)
        print(f"  -> Inserted {img_path.name}")

        is_last = (index + 1) == len(image_paths)
        if (index + 1) % images_per_page == 0 and not is_last:
            doc.add_page_break()

    doc.save(output_word_path)
    print(f"\n[DONE] Successfully saved Word document to '{output_word_path}'")


def create_word_from_images(image_folder: str, output_word_path: str, images_per_page: int = 2):
    """
    Same as before: point it at a folder and it grabs every image inside.
    Still a thin wrapper around build_word_doc.
    """
    img_dir = Path(image_folder)

    if not img_dir.exists():
        raise FileNotFoundError(f"Image folder not found: {img_dir}")

    valid_extensions = {".png", ".jpg", ".jpeg"}
    images = [f for f in img_dir.iterdir() if f.suffix.lower() in valid_extensions]
    images.sort()

    if not images:
        print(f"No images found in '{img_dir.resolve()}'.")
        return

    build_word_doc(images, output_word_path, images_per_page=images_per_page)


if __name__ == "__main__":
    IMAGE_DIR = r"C:\Users\HP\PROJECTS\scansort\extracted_images"
    OUTPUT_DOCX = r"C:\Users\HP\PROJECTS\scansort\images_report.docx"

    create_word_from_images(IMAGE_DIR, OUTPUT_DOCX)