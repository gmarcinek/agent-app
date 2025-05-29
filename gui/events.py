from textual.message import Message
from pathlib import Path

class FileOpenRequest(Message):
    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path