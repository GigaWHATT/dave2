from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from concurrent.futures import Future


# ----------CONSENT DIALOG BOX-----------
class ConsentDialog(QDialog):
    """ Consent dialog box class for user consent on tool calls

    Args:
        QDialog (class): dialog box
    """

    def __init__(self, message: str):
        """ Initialises consent dialog box

        Args:
            message (str): message to display to user for consent
        """
        super().__init__()

        # Window style
        self.setWindowTitle("Consent Required")
        layout = QVBoxLayout()

        # Display message
        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.result: Future[str] = Future()

        # Buttons for user consent
        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(lambda: self.finish("Y"))
        layout.addWidget(yes_button)

        no_button = QPushButton("No")
        no_button.clicked.connect(lambda: self.finish("N"))
        layout.addWidget(no_button)

        self.setLayout(layout)

    def closeEvent(self, event):
        """Handle dialog close (e.g., user clicks 'X')"""
        if not self.result.done():
            self.result.set_result("N")  # Default to "No" if closed
        super().closeEvent(event)

    def finish(self, value: str):
        """ Sets the result of the Future and closes the dialog

        Args:
            value (str): consent
        """
        if not self.result.done():
            self.result.set_result(value)
        self.accept()
