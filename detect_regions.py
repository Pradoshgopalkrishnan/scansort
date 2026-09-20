# detect_regions.py
# Phase 4 — scanned-page diagram detection
# Updated to use the modern `pymupdf` import instead of the legacy `fitz` alias

import pymupdf  # modern import name (fitz still works, but pymupdf is preferred going forward)
import numpy as np
import cv2
from pathlib import Path


def render_page_as_image(pdf_path: str, page_number: int, zoom: float = 2.0):
    """
    Renders one PDF page to a raster image, the way a screenshot would.
    zoom=2.0 roughly doubles resolution vs default (~144 DPI) — higher zoom
    means clearer detail for detection later, at the cost of speed.
    """
    doc = pymupdf.open(pdf_path)
    page = doc[page_number]
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    doc.close()
    return pix


def pixmap_to_cv_image(pix):
    """
    Converts a PyMuPDF pixmap directly into an OpenCV (NumPy array) image,
    entirely in memory — no temp file written to disk.
    """
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:  # has an alpha channel
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img


def preprocess_for_detection(img):
    """
    Converts to grayscale, smooths out scan noise, then thresholds
    so ink becomes solid white and background becomes solid black.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # THRESH_BINARY_INV: anything darker than 200 becomes white (255), rest becomes black
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
    return thresh


def find_candidate_regions(thresh_img):
    """
    Merges nearby ink marks into solid blobs, then finds the outline
    (contour) of each blob. Returns a list of (x, y, width, height) boxes.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    dilated = cv2.dilate(thresh_img, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]
    return boxes


def draw_debug_boxes(img, boxes, color=(0, 0, 255)):
    """Draws a rectangle for every candidate region, for visual debugging."""
    debug_img = img.copy()
    for (x, y, w, h) in boxes:
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 3)
    return debug_img


def filter_diagram_candidates(boxes, page_shape):
    """
    Filters raw candidate boxes down to ones that look like diagrams
    rather than text paragraphs, using size and shape heuristics.
    TUNE the threshold numbers below against your own real manuals.
    """
    page_area = page_shape[0] * page_shape[1]
    keep = []

    for (x, y, w, h) in boxes:
        area_ratio = (w * h) / page_area
        aspect_ratio = w / h

        if area_ratio < 0.02:
            continue  # too small — likely a stray mark, not a real diagram
        if area_ratio > 0.85:
            continue  # too big — likely the whole page merged into one blob
        if aspect_ratio > 5 or aspect_ratio < 0.2:
            continue  # extremely wide/tall — usually a line of text, not a diagram

        keep.append((x, y, w, h))

    return keep


def extract_diagrams_from_scanned_pdf(pdf_path: str, output_dir: str = "extracted_diagrams") -> list[Path]:
    """
    Full Phase 4 pipeline: renders every page, detects likely diagram
    regions, crops and saves them. Returns saved file paths — same
    return shape as extract_images_from_pdf, so the GUI can treat
    both sources interchangeably.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    doc = pymupdf.open(pdf_path)
    num_pages = len(doc)
    doc.close()

    saved_paths = []

    for page_num in range(num_pages):
        pix = render_page_as_image(pdf_path, page_num)
        img = pixmap_to_cv_image(pix)
        thresh = preprocess_for_detection(img)
        boxes = find_candidate_regions(thresh)
        filtered = filter_diagram_candidates(boxes, img.shape)

        for i, (x, y, w, h) in enumerate(filtered):
            cropped = img[y:y + h, x:x + w]
            filename = f"page_{page_num:03d}_region_{i:02d}.png"
            filepath = output_path / filename
            cv2.imwrite(str(filepath), cropped)
            saved_paths.append(filepath)

        print(f"Page {page_num + 1}/{num_pages}: found {len(filtered)} diagram(s)")

    return saved_paths

def pixmap_to_cv_image(pix):
    """
    Converts a PyMuPDF pixmap directly into an OpenCV (NumPy array) image,
    entirely in memory — no temp file written to disk.
    """
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:  # has an alpha channel
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img

if __name__ == "__main__":
    pix = render_page_as_image("test_scanned.pdf", page_number=0)
    img = pixmap_to_cv_image(pix)
    print("Image shape:", img.shape)  # (height, width, 3) confirms a valid color image

