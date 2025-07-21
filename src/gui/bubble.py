import re
from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QTimer


# ----------CHAT BUBBLE-----------
class ChatBubble(QLabel):
    """ Chat Bubble class for displaying messages in window

    Args:
        QLabel (class): displays text
    """

    def __init__(self, full_text, is_user=False, on_done=None):
        """ Initializes chat bubble

        Args:
            full_text (str): text displayed in final bubble
            is_user (bool, optional): differentiates agent and user chat bubbles (colour). Defaults to False.
        """
        super().__init__()
        self.full_text = full_text
        self.displayed_text = ""
        self.index = 0
        self.setWordWrap(True)
        colour = "#ca66a0" if is_user else "#747bda"
        radius = "10px 10px 0px 10px" if is_user else "10px 10px 10px 0px"
        self.setStyleSheet(
            f"padding: 10px; margin: 5px; border-radius: {radius}; background-color: {colour};"
            "max-width: 600px;"  # Limit bubble width for readability
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Maximum)
        self.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML formatting
        self.setOpenExternalLinks(True)  # <-- This makes links open in browser
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(20)  # Adjust for speed
        self.on_done = on_done
        self.done = False

    def format_brackets(self, text) -> str:
        """ Uses HTML to format text before displaying it on the window

        Args:
            text (str): text to format

        Returns:
            str: text formatted in HTML
        """

        # Style [Called tool ...] with italic font weight
        called_tool = re.sub(
            r"\[Called tool ([^\]]+)\]",
            r'<span style="color:#fff; font-style:italic;">[Called tool \1]</span>',
            text
        )

        # Remove double asterisks
        no_stars = called_tool.replace("**", "")

        # Make url's clickable "(here)"
        url_pattern = r"\((https?://[^\s]+)\)"
        links = re.sub(
            url_pattern, r'(<a href="\1" style="color:#ca66a0; text-decoration:underline;">here</a>)', no_stars)

        # Replace newlines with <br>
        html_text = links.replace('\n', '<br>')
        return html_text

    def update_text(self):
        """ Progressively updates the text in the bubble
        """
        if self.index < len(self.full_text):
            self.displayed_text += self.full_text[self.index]
            formatted = self.format_brackets(self.displayed_text)
            self.setText(formatted)
            self.index += 1
            # Call on_done with progressive scroll
            self.on_done(progressive=True)
        else:
            self.timer.stop()
            formatted = self.format_brackets(self.displayed_text)
            self.setText(formatted)
            self.done = True
            self.on_done(progressive=False)  # Call on_done with final scroll