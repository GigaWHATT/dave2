import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QLineEdit, QDialog, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon
import asyncio
from asyncio import Future
from loguru import logger
from qasync import asyncSlot


class ChatBubble(QLabel):
    def __init__(self, full_text, is_user=False):
        super().__init__()
        self.full_text = full_text
        self.displayed_text = ""
        self.index = 0
        self.setWordWrap(True)
        colour = "#df94c0" if is_user else "#747bda"
        self.setStyleSheet(
            f"padding: 10px; border-radius: 10px; background-color: {colour};")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(20)  # Adjust for speed

    def update_text(self):
        if self.index < len(self.full_text):
            self.displayed_text += self.full_text[self.index]
            self.setText(self.displayed_text)
            self.index += 1
        else:
            self.timer.stop()


class ChatWindow(QWidget):
    def __init__(self, client):
        super().__init__()
        
        self.setWindowIcon(QIcon("../dave.png"))  # Set your icon here
        self.setWindowTitle("Dave")
        self.setMinimumSize(400, 600)
        self.client = client

        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.chat_container)
        self.layout.addWidget(self.scroll_area)

        self.line = QLineEdit(self)
        self.layout.addWidget(self.line)
        self.line.returnPressed.connect(self.on_send_clicked)

        self.send_button = QPushButton("Send Message")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.layout.addWidget(self.send_button)
    """
    def closeEvent(self,event):
        event.accept()
        QTimer.singleShot(0, lambda: asyncio.create_task(self.shutdown()))
    """
    """
    async def shutdown(self):
        try:
            logger.info("Shutting down application...")
            await self.client.cleanup()
            logger.info("Client cleanup completed.")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            QApplication.quit()
            logger.info("Application shutdown completed.")
    """
    
    def resizeEvent(self,event):
        size = event.size()
        super().resizeEvent(event)
        
        print(size)
    
    @asyncSlot()
    async def on_send_clicked(self):
        await self.send_message()
        
    async def send_message(self):
        text = "You:\n\n"
        text += self.line.text()
        text += '\n'
        self.line.clear()
        user_bubble = ChatBubble(text, is_user=True)
        self.chat_layout.addWidget(user_bubble)
        
        # Create a container and align right
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(user_bubble)
        layout.setAlignment(user_bubble, Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.addWidget(container)

        """
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum())
        )
        """
        await asyncio.sleep(0.1)  # Allow GUI to update
        response = await self.handle_query(text)
    
    async def ask_user_consent(self, message: str) -> str:
        dialog = ConsentDialog(message)
        dialog.show()
        #await asyncio.sleep(0.1)  # let the dialog render
        return await dialog.result

    
    async def handle_query(self, query: str):
        try:
            logger.info("Handle query launched")
            response = await self.client.process_query(query)
            await self.receive_message(response)
        except Exception as e:
            await self.receive_message(f'Error: {e}')

    async def receive_message(self, response):
        text = "Dave:\n"
        text += response
        logger.info("Called receive message")
        ai_bubble = ChatBubble(text)
        self.chat_layout.addWidget(ai_bubble)
        # Create a container and align left
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(ai_bubble)
        layout.setAlignment(ai_bubble, Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.addWidget(container)
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum())
        )
        logger.info("End of receive message call")

class ConsentDialog(QDialog):
    def __init__(self, message: str):
        super().__init__()
        self.setWindowTitle("Consent Required")
        layout = QVBoxLayout()

        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.result: Future[str] = Future()

        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(lambda: self.finish("Y"))
        layout.addWidget(yes_button)

        no_button = QPushButton("No")
        no_button.clicked.connect(lambda: self.finish("N"))
        layout.addWidget(no_button)

        self.setLayout(layout)

    def finish(self, value: str):
        if not self.result.done():
            self.result.set_result(value)
        self.accept()
