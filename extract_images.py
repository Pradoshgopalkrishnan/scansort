from pathlib import Path
import pymupdf  # Fix: Updated to the new API standard to remove the warning


def extract_images_from_pdf(pdf_path: str, output_dir: str = "extracted_images"):
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Source file not found: {pdf_path}")

    out_folder = Path(output_dir)
    out_folder.mkdir(parents=True, exist_ok=True)

    # Fix: Updated to use pymupdf
    doc = pymupdf.open(pdf_file)
    print(f"[INFO] Document opened: {pdf_file.name}")
    print(f"[INFO] Total Pages: {doc.page_count}\n")

    seen_xrefs = set()
    extracted_count = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1

        image_list = page.get_images(full=True)

        if not image_list:
            print(f"Page {page_num}: No embedded images found.")
            continue

        print(f"Page {page_num}: Found {len(image_list)} image reference(s).")

        for img_idx, img_info in enumerate(image_list, start=1):
            xref = img_info[0]

            if xref in seen_xrefs:
                print(f"  -> Skipping duplicate image object (xref: {xref})")
                continue
            seen_xrefs.add(xref)

            base_image = doc.extract_image(xref)
            
            # Fix: The correct dictionary key for the binary data is "image", not "bytes"
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            dimensions = f"{base_image['width']}x{base_image['height']}"

            filename = f"page_{page_num:03d}_img_{img_idx:02d}_xref{xref}.{image_ext}"
            file_path = out_folder / filename

            with open(file_path, "wb") as img_file:
                img_file.write(image_bytes)

            extracted_count += 1
            print(f"  -> Saved: {filename} ({dimensions}, format: {image_ext})")

    doc.close()
    print(f"\n[DONE] Finished! Saved {extracted_count} unique image(s) to '{out_folder.resolve()}'")


if __name__ == "__main__":
    TARGET_PDF = r"C:\Users\HP\PROJECTS\scansort\test_sample.pdf"
    extract_images_from_pdf(TARGET_PDF)