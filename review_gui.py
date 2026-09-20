"""
DiagX — Phase 3: Review GUI

Drag a PDF onto the window -> extracted images show as a checkbox grid ->
"Export" sends only the checked ones to Phase 2's docx logic.

No OCR here on purpose (that's Phase 5) — this is manual selection only.
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea,
    QGridLayout, QLabel, QCheckBox, QPushButton, QFileDialog, QMessageBox,
)

from extract_images import extract_images_from_pdf
from images_to_word import build_word_doc

THUMB_SIZE = 160
GRID_COLUMNS = 4
DEFAULT_EXPORT_LABEL = "Export Checked Images to Word"


class ImageTile(QWidget):
    """One thumbnail + checkbox for a single extracted image."""

    def __init__(self, image_path: Path):
        super().__init__()
        self.image_path = image_path

        layout = QVBoxLayout(self)

        pixmap = QPixmap(str(image_path)).scaled(
            THUMB_SIZE, THUMB_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        thumb_label = QLabel()
        thumb_label.setPixmap(pixmap)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(image_path.name)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.checkbox = QCheckBox("Keep")
        self.checkbox.setChecked(True)  # default: keep everything, user unchecks what to drop

        layout.addWidget(thumb_label)
        layout.addWidget(name_label)
        layout.addWidget(self.checkbox)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()


class ReviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiagX — Review Extracted Images")
        self.resize(900, 650)
        self.setAcceptDrops(True)

        self.tiles: list[ImageTile] = []
        self.output_dir = Path("extracted_images")

        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)

        self.hint_label = QLabel("Drag and drop a PDF here to extract its images")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("font-size: 16px; padding: 30px; color: #666;")
        outer_layout.addWidget(self.hint_label)

        # Scrollable grid of thumbnails
        self.grid = QGridLayout()
        grid_container = QWidget()
        grid_container.setLayout(self.grid)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_container)
        outer_layout.addWidget(scroll, stretch=1)

        self.export_button = QPushButton(DEFAULT_EXPORT_LABEL)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_to_word)
        outer_layout.addWidget(self.export_button)

    # --- Drag-and-drop handlers ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        pdf_paths = [u.toLocalFile() for u in urls if u.toLocalFile().lower().endswith(".pdf")]
        if not pdf_paths:
            return
        # Only the first PDF dropped is handled — batch mode (multiple PDFs at once) is Phase 7
        self.load_pdf(pdf_paths[0])

    # --- Core logic ---

    def load_pdf(self, pdf_path: str):
        self.hint_label.setText(f"Extracting images from {Path(pdf_path).name} ...")
        self.setCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()  # repaint before the extraction blocks the UI thread

        try:
            image_paths = extract_images_from_pdf(pdf_path, str(self.output_dir))
        except Exception as exc:
            self.unsetCursor()
            QMessageBox.critical(self, "Extraction failed", str(exc))
            self.hint_label.setText("Drag and drop a PDF here to extract its images")
            return

        self.unsetCursor()

        if not image_paths:
            self.hint_label.setText("No embedded images found in that PDF.")
            return

        self.populate_grid(image_paths)
        self.hint_label.setText(
            f"Loaded {len(image_paths)} image(s). Uncheck any you don't want, then export."
        )
        self.export_button.setEnabled(True)

    def populate_grid(self, image_paths):
        # Clear tiles from any previous drop before loading new ones
        for tile in self.tiles:
            self.grid.removeWidget(tile)
            tile.deleteLater()
        self.tiles.clear()

        for index, path in enumerate(image_paths):
            tile = ImageTile(Path(path))
            self.tiles.append(tile)
            row, col = divmod(index, GRID_COLUMNS)
            self.grid.addWidget(tile, row, col)

    def export_to_word(self):
        checked_paths = [tile.image_path for tile in self.tiles if tile.is_checked()]

        if not checked_paths:
            QMessageBox.warning(self, "Nothing selected", "Check at least one image before exporting.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Word Document", "images_report.docx", "Word Documents (*.docx)"
        )
        if not save_path:
            return

        # Visible feedback so the window doesn't look frozen while it saves
        self.export_button.setEnabled(False)
        self.export_button.setText("Exporting...")
        self.hint_label.setText(f"Exporting {len(checked_paths)} image(s) to Word...")
        self.setCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()  # force a repaint before the blocking save call

        try:
            build_word_doc(checked_paths, save_path)
        except Exception as exc:
            self.unsetCursor()
            self.export_button.setEnabled(True)
            self.export_button.setText(DEFAULT_EXPORT_LABEL)
            self.hint_label.setText("Export failed — fix the issue and try again.")
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        self.unsetCursor()
        self.export_button.setEnabled(True)
        self.export_button.setText(DEFAULT_EXPORT_LABEL)
        self.hint_label.setText(f"Exported {len(checked_paths)} image(s) to {Path(save_path).name}")
        self.show_export_complete_dialog(save_path, len(checked_paths))

    def show_export_complete_dialog(self, save_path: str, count: int):
        """A dedicated window confirming the export, with a clear choice:
        keep working in the app, or close it entirely."""
        box = QMessageBox(self)
        box.setWindowTitle("Export Complete")
        box.setText(f"Saved {count} image(s) to:\n{save_path}")

        continue_button = box.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
        exit_button = box.addButton("Exit App", QMessageBox.ButtonRole.DestructiveRole)
        box.setDefaultButton(continue_button)

        box.exec()

        if box.clickedButton() is exit_button:
            QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    window = ReviewWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


