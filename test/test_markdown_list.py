import os
from unittest import TestCase, mock
from src.markdown_list import MarkdownList

TEST_FILE = 'test/README.md'


class TestMarkdownList(TestCase):
    def setUp(self) -> None:
        self.md_list = MarkdownList()
        return super().setUp()

    def tearDown(self) -> None:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        return super().tearDown()

    def test_load_existing_no_README(self):
        self.md_list.load_existing()
        assert self.md_list.original_contents == []

    def test_load_existing_no_contents(self):
        self.md_list.load_existing()
        assert self.md_list.original_contents == []

    def test_load_existing_README_has_content(self):
        original_contents = [
            '# KATTIS SOLUTIONS\n',
            'This repository includes my solutions to Kattis problems'
        ]
        with open(TEST_FILE, 'w') as md_file:
            md_file.writelines(original_contents)
        self.md_list.load_existing()
        assert self.md_list.original_contents == original_contents
