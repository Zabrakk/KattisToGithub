import os
from typing import List
from pathlib import Path
from copy import deepcopy
from unittest import TestCase
from src.constants import *
from src.markdown_list import MarkdownList
from constants import SOLVED_PROBLEMS, TEST_DIR

TEST_FILE = TEST_DIR + '/README.md'
README_LIST_START = lambda n: [README_LIST_TITLE, KTG_AD, SEPARATOR, README_NUM_SOLVED(n), README_LIST_COLUMN_TITLES, README_LIST_POSITIONING]


class TestMarkdownList(TestCase):
    def setUp(self) -> None:
        self.md_list = MarkdownList(directory=Path(TEST_DIR), solved_problems=deepcopy(SOLVED_PROBLEMS))
        return super().setUp()

    def tearDown(self) -> None:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        return super().tearDown()

    def __write_to_README(self, contents: List[str]) -> None:
        with open(TEST_FILE, 'w') as md_file:
            md_file.writelines(contents)

    def __read_README(self) -> List[str]:
        with open(TEST_FILE, 'r') as md_file:
            return md_file.readlines()

    def test_load_existing_README_contents_no_README(self):
        self.md_list._load_existing_README_contents()
        assert self.md_list.original_contents == []
        assert self.md_list.new_contents == ['\n'] + README_LIST_START(3)

    def test_load_existing_README_contents_no_contents(self):
        self.__write_to_README([])
        self.md_list._load_existing_README_contents()
        assert self.md_list.original_contents == []
        assert self.md_list.new_contents == ['\n'] + README_LIST_START(3)

    def test_load_existing_README_contents_README_has_content(self):
        original_contents = [
            '# KATTIS SOLUTIONS\n',
            'This repository includes my solutions to Kattis problems'
        ]
        self.__write_to_README(original_contents)
        self.md_list._load_existing_README_contents()
        assert self.md_list.original_contents == original_contents
        assert self.md_list.new_contents == original_contents + ['\n'] + README_LIST_START(3)

    def test_load_existing_README_contents_README_already_has_list(self):
        original_contents = [
            '# KATTIS SOLUTIONS\n',
            'This repository includes my solutions to Kattis problem\n',
            README_LIST_TITLE,
            'line1\n',
            'line2\n'
        ]
        self.__write_to_README(original_contents)
        self.md_list._load_existing_README_contents()
        assert self.md_list.original_contents == original_contents
        assert self.md_list.new_contents == original_contents[:2] + README_LIST_START(3)

    def test_sort_solved_problems_by_difficulty(self):
        expected_result = ['Hard', 'Medium', 'Easy', 'Easy']
        self.md_list._sort_solved_problems_by_difficulty()
        for i, entry in enumerate(self.md_list.solved_problems):
            assert entry.difficulty == expected_result[i]

    def test_create_solved_problem_list(self):
        solved_problem_list = self.md_list._create_solved_problem_list()
        assert len(solved_problem_list) == 3
        for i, entry in enumerate(solved_problem_list):
            solutions = self.__create_problem_list_entry(i)
            expected_result = f'|[{SOLVED_PROBLEMS[i].name}]({SOLVED_PROBLEMS[i].problem_link})|{SOLVED_PROBLEMS[i].difficulty}|' + solutions + '\n'
            assert entry == expected_result

    def __create_problem_list_entry(self, i: int) -> str:
        return ' '.join([f'[{language}](Solutions/{filename})' for filename, language in SOLVED_PROBLEMS[i].filename_language_dict.items()])

    def test_save_contents_to_README(self):
        contents_to_save = README_LIST_START(0) + ['|1|2|3|\n']
        self.md_list._save_contents_to_README(contents_to_save)
        self.__read_README() == contents_to_save

    def test_create(self):
        self.__write_to_README(['# KATTIS SOLUTIONS\n', 'My solutions.'])
        self.md_list.create()
        assert self.__read_README() == ['# KATTIS SOLUTIONS\n', 'My solutions.\n'] + README_LIST_START(3) + [
            f'|[{SOLVED_PROBLEMS[2].name}]({SOLVED_PROBLEMS[2].problem_link})|{SOLVED_PROBLEMS[2].difficulty}|' + self.__create_problem_list_entry(2) + '\n',
            f'|[{SOLVED_PROBLEMS[0].name}]({SOLVED_PROBLEMS[0].problem_link})|{SOLVED_PROBLEMS[0].difficulty}|' + self.__create_problem_list_entry(0) + '\n',
            f'|[{SOLVED_PROBLEMS[1].name}]({SOLVED_PROBLEMS[1].problem_link})|{SOLVED_PROBLEMS[1].difficulty}|' + self.__create_problem_list_entry(1) + '\n'
        ]

    def test_should_add_and_commit_property_true(self):
        self.md_list.create()
        assert self.md_list.should_add_and_commit is True

    def test_should_add_and_commit_property_false(self):
        self.md_list.create()
        self.md_list.create()
        assert self.md_list.should_add_and_commit is False
