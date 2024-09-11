import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QGraphicsDropShadowEffect,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtGui import QFont, QCursor, QColor
from PyQt5.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve
from sec_pdf_parser import extract_sec_data
from portfolio_parser import process_portfolio
from xml_generator import generate_xml



# Helper function to blend colors (used to simulate the fade effect)
def blend_colors(start_color, end_color, factor):
    return QColor(
        int(start_color.red() * (1 - factor) + end_color.red() * factor),
        int(start_color.green() * (1 - factor) + end_color.green() * factor),
        int(start_color.blue() * (1 - factor) + end_color.blue() * factor),
    )

def setup_button_hover_effects(button):
    # Change cursor to hand when hovering
    button.setCursor(QCursor(Qt.PointingHandCursor))

    # Set up the shadow effect for the button
    shadow_effect = QGraphicsDropShadowEffect(button)
    shadow_effect.setBlurRadius(10)  # Initially no shadow
    shadow_effect.setColor(QColor(26, 115, 232, 200))  # Shadow color (semi-transparent)
    shadow_effect.setOffset(0, 0)  # No offset for shadow
    button.setGraphicsEffect(shadow_effect)

    # Colors for the fade animation
    default_color = QColor("#4ca3f3")
    hover_color = QColor("#4003ff")
    animation_duration = 300  # Duration of the fade effect in milliseconds
    steps = 30  # Number of steps for the animation
    interval = animation_duration // steps  # Time interval between steps

    # Function to apply background color
    def set_background_color(color):
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color.name()};
                color: white;
                border-radius: 10px;
            }}
            """
        )

    # Fade in effect (hover)
    def fade_in():
        step = 0

        def update_fade_in():
            nonlocal step
            factor = step / steps
            blended_color = blend_colors(default_color, hover_color, factor)
            set_background_color(blended_color)
            step += 1
            if step > steps:
                fade_in_timer.stop()

        fade_in_timer = QTimer(button)
        fade_in_timer.timeout.connect(update_fade_in)
        fade_in_timer.start(interval)

    # Fade out effect (hover leave)
    def fade_out():
        step = 0

        def update_fade_out():
            nonlocal step
            factor = step / steps
            blended_color = blend_colors(hover_color, default_color, factor)
            set_background_color(blended_color)
            step += 1
            if step > steps:
                fade_out_timer.stop()

        fade_out_timer = QTimer(button)
        fade_out_timer.timeout.connect(update_fade_out)
        fade_out_timer.start(interval)

    # Install event filter for hover effect
    def eventFilter(widget, event):
        if event.type() == QEvent.Enter:  # On hover
            fade_in()

            # Animate shadow from 10 to 30 blur radius
            shadow_effect.setBlurRadius(30)

        elif event.type() == QEvent.Leave:  # On leave
            fade_out()

            # Animate shadow back from 30 to 10 blur radius
            shadow_effect.setBlurRadius(10)

        return False  # Keep the default behavior

    # Attach the event filter to the button
    button.installEventFilter(button)
    button.eventFilter = eventFilter

class SEC13FXMLGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.sec_pdf_path = None
        self.portfolio_excel_path = None

    def initUI(self):
        self.setWindowTitle("SEC 13F XML Generator")

        # Increase window size
        self.setGeometry(500, 200, 600, 500)

        # Font configuration
        font = QFont("Arial", 14)

        # Layout
        layout = QVBoxLayout()

        # Labels to display selected file paths
        self.pdf_label = QLabel("SEC 13F PDF: Not selected", self)
        self.pdf_label.setFont(font)

        self.excel_label = QLabel("Portfolio Excel: Not selected", self)
        self.excel_label.setFont(font)

        # Buttons to browse files with full window width
        self.pdf_button = QPushButton("Select SEC 13F PDF", self)
        self.pdf_button.setFont(font)
        self.pdf_button.setFixedHeight(60)  # Set only the height
        self.pdf_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4ca3f3;
                color: white;
                border-radius: 10px;
            }
        """
        )
        setup_button_hover_effects(self.pdf_button)
        self.pdf_button.clicked.connect(self.select_sec_pdf)

        self.excel_button = QPushButton("Select Portfolio Excel", self)
        self.excel_button.setFont(font)
        self.excel_button.setFixedHeight(60)  # Set only the height
        self.excel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4ca3f3;
                color: white;
                border-radius: 10px;
            }
        """
        )
        setup_button_hover_effects(self.excel_button)
        self.excel_button.clicked.connect(self.select_portfolio_excel)

        # Button to generate XML with full window width
        self.generate_button = QPushButton("Generate XML", self)
        self.generate_button.setFont(font)
        self.generate_button.setFixedHeight(60)  # Set only the height
        self.generate_button.setStyleSheet(
            """
            QPushButton {
                
                background-color: #f39c12;
                color: white;
                border-radius: 10px;
            }
        """
        )
        setup_button_hover_effects(self.generate_button)
        self.generate_button.clicked.connect(self.generate_xml_report)

        # Add widgets to the layout
        layout.addWidget(self.pdf_label)
        layout.addWidget(self.pdf_button)
        layout.addWidget(self.excel_label)
        layout.addWidget(self.excel_button)
        spacer = QSpacerItem(20, 30, QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout.addItem(spacer)
        layout.addWidget(self.generate_button)

        # Set layout
        self.setLayout(layout)

    def select_sec_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select SEC 13F PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)",
            options=options,
        )
        if file_name:
            self.sec_pdf_path = file_name
            self.pdf_label.setText(f"SEC 13F PDF: {os.path.basename(file_name)}")

    def select_portfolio_excel(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Portfolio Excel File",
            "",
            "Excel Files (*.xlsx);;All Files (*)",
            options=options,
        )
        if file_name:
            self.portfolio_excel_path = file_name
            self.excel_label.setText(f"Portfolio Excel: {os.path.basename(file_name)}")

    def generate_xml_report(self):
        if not self.sec_pdf_path or not self.portfolio_excel_path:
            QMessageBox.warning(
                self,
                "Error",
                "Please select both SEC 13F PDF and Portfolio Excel files.",
            )
            return

        # Prompt user to select the output file path
        options = QFileDialog.Options()
        output_xml_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save XML File",
            "",
            "XML Files (*.xml);;All Files (*)",
            options=options,
        )

        if not output_xml_path:
            # User canceled the save dialog
            return

        # Step 1: Extract data from SEC 13F PDF
        try:
            sec_data = extract_sec_data(self.sec_pdf_path)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to extract data from SEC PDF: {str(e)}"
            )
            return

        # Step 2: Process client portfolio
        try:
            portfolio_data = process_portfolio(self.portfolio_excel_path)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to process portfolio: {str(e)}"
            )
            return

        # Step 3: Generate XML
        try:
            generate_xml(sec_data, portfolio_data, output_xml_path)
            QMessageBox.information(
                self,
                "Success",
                f"XML report generated successfully at {output_xml_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate XML: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SEC13FXMLGenerator()
    window.show()
    sys.exit(app.exec_())
