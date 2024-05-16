import os
from pathlib import Path


class MarkdownList:
    def __init__(self, directory: Path) -> None:
        self.__filepath = directory / 'README.md'

    def load_existing_README(self):
        if os.path.exists(self.__filepath):
            with open(self.__filepath, 'r') as md_file:
                self.original_contents = md_file.readlines()
        else:
            self.original_contents = []

    def create(self):
        pass