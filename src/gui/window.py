from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLineEdit, QPushButton, QLabel, QSizePolicy, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import asyncio
from .consent import ConsentDialog
from .bubble import ChatBubble

from qasync import asyncSlot


# ----------CHAT WINDOW-----------
class ChatWindow(QWidget):
    """ Displays chat interface

    Args:
        QWidget (class): container
    """

    def __init__(self, client):
        """ Initialise chat window
        Args:
            client (MCPClient): client used to communicate with MCP server
        """

        super().__init__()

        # Window style
        self.setWindowIcon(QIcon("../dave.png"))
        self.setWindowTitle("Dave")
        self.setMinimumSize(400, 600)
        self.setMaximumSize(800, 900)  # Set your preferred max size

        # Disable maximize button
        self.setWindowFlags(self.windowFlags() & ~
                            Qt.WindowType.WindowMaximizeButtonHint)

        self.setStyleSheet(
            "background-color: #1a1a1a; color: #fff; font-family: Arial, sans-serif; font-size: 14px;")

        self.client = client

        # Layout
        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.chat_container)
        self.layout.addWidget(self.scroll_area)

        # User input
        self.line = QLineEdit(self)
        self.layout.addWidget(self.line)
        # send message on Enter press
        self.line.returnPressed.connect(self.on_send_clicked)

        self.send_button = QPushButton("Send Message")
        # send message on send button click
        self.send_button.clicked.connect(self.on_send_clicked)
        self.layout.addWidget(self.send_button)

        self.line.setStyleSheet("""
            background-color: #2a2a2a;
            color: #fff;
            border: 1px solid #555;
            padding: 8px;
            border-radius: 6px;
        """)

        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #747bda;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #8b8ff0;
            }
        """)

        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #2e2e2e;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def scroll_to_bottom(self, progressive=False):
        """ Manages window scrolling

        Args:
            progressive (bool, optional): scroll during message send or at the end. Defaults to False.
        """
        scrollbar = self.scroll_area.verticalScrollBar()
        if progressive:
            new_value = min(scrollbar.value()+3, scrollbar.maximum())
            scrollbar.setValue(new_value)
        else:
            # Scroll to bottom
            scrollbar.setValue(scrollbar.maximum())

    def resizeEvent(self, event):
        """ On resize of window, print new size

        Args:
            event (event): Contains resize event information
        """
        size = event.size()
        super().resizeEvent(event)
        print(size)

    @asyncSlot()
    async def on_send_clicked(self):
        """ Handles async await for send_message()
        """
        await self.send_message()

    async def send_message(self):
        """ Send message to MCP client from user for processing and display message
        """
        # Formatting
        text = self.line.text()

        # Display message
        self.line.clear()
        user_bubble = ChatBubble(
            text, is_user=True, on_done=self.scroll_to_bottom)

        # Name label above bubble
        name_label = QLabel("User")
        name_label.setStyleSheet("color: #ca66a0; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Vertical layout for name above bubble
        v_layout = QVBoxLayout()
        v_layout.addWidget(name_label)
        v_layout.addWidget(user_bubble)
        v_layout.setSpacing(2)
        v_layout.setContentsMargins(0, 0, 0, 0)

        # Horizontal layout for alignment
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.addStretch()  # Push to right
        h_layout.addLayout(v_layout)
        h_layout.setContentsMargins(0, 0, 0, 0)
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.chat_layout.addWidget(container)
        while user_bubble.done is False:
            await asyncio.sleep(0.01)  # Allow GUI to update
        response = await self.handle_query(text)  # Process query

    async def ask_user_consent(self, message: str) -> str:
        """ Displays user consent dialog box

        Args:
            message (str): informs user on tool call and arguments needing consent

        Returns:
            str: "Y" for yes, "N" for no
        """
        dialog = ConsentDialog(message)
        dialog.show()
        return await dialog.result

    async def handle_query(self, query: str):
        """ Launch process query and display result in chat window

        Args:
            query (str): user query
        """
        try:
            
            response = await self.client.process_query(query)
            await self.receive_message(response)
        except Exception as e:
            await self.receive_message(f'Error: {e}')

    async def receive_message(self, response):
        """ Display message by agent

        Args:
            response (str): result from user query processing
        """

        # Formatting
        text = response

        # Create bubble
        ai_bubble = ChatBubble(text, on_done=self.scroll_to_bottom)

        name_label = QLabel("Dave")
        name_label.setStyleSheet("color: #747bda; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        v_layout = QVBoxLayout()
        v_layout.addWidget(name_label)
        v_layout.addWidget(ai_bubble)
        v_layout.setSpacing(2)
        v_layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.addLayout(v_layout)
        h_layout.addStretch()  # Push to left
        h_layout.setContentsMargins(0, 0, 0, 0)
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.chat_layout.addWidget(container)