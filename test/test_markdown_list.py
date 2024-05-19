import os
from pathlib import Path
from unittest import TestCase, mock
from src.markdown_list import MarkdownList
from src.solved_problem import SolvedProblem, ProblemStatus

TEST_DIR = 'test'
TEST_FILE = TEST_DIR + '/README.md'
SOLVED_PROBLEMS = [
    SolvedProblem(
        name='Problem1',
        difficulty='Medium',
        status=ProblemStatus.CODE_FOUND,
        problem_link='problem_link1',
        filename_language_dict={'test1.py': 'Python 3', 'test1.cpp': 'C++'}
    ),
    SolvedProblem(
        name='Problem2',
        difficulty='Easy',
        status=ProblemStatus.CODE_FOUND,
        problem_link='problem_link2',
        filename_language_dict={'test2.py': 'Python 3'}
    ),
    SolvedProblem(
        name='Problem3',
        difficulty='Hard',
        status=ProblemStatus.CODE_FOUND,
        problem_link='problem_link3',
        filename_language_dict={'test3.py': 'Python 3'}
    ),
    SolvedProblem(
        name='Problem4',
        difficulty='Easy',
        status=ProblemStatus.CODE_NOT_FOUND,
        problem_link='problem_link4'
    ),
]


class TestMarkdownList(TestCase):
    def setUp(self) -> None:
        self.md_list = MarkdownList(directory=Path(TEST_DIR), solved_problems=SOLVED_PROBLEMS)
        return super().setUp()

    def tearDown(self) -> None:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        return super().tearDown()

    def test_load_existing_README_contents_no_README(self):
        self.md_list.load_existing_README_contents()
        assert self.md_list.original_contents == []
        assert self.md_list.new_contents == []

    def test_load_existing_README_contents_no_contents(self):
        self.md_list.load_existing_README_contents()
        assert self.md_list.original_contents == []
        assert self.md_list.new_contents == []

    def test_load_existing_README_contents_README_has_content(self):
        original_contents = [
            '# KATTIS SOLUTIONS\n',
            'This repository includes my solutions to Kattis problems'
        ]
        with open(TEST_FILE, 'w') as md_file:
            md_file.writelines(original_contents)
        self.md_list.load_existing_README_contents()
        assert self.md_list.original_contents == original_contents
        assert self.md_list.new_contents == original_contents + ['\n'] + ['## Solved Problems\n'] + ['<sub><i>Created with [KattisToGithub](https://github.com/Zabrakk/KattisToGithub)</i></sub>\n']

    def test_load_existing_README_contents_README_already_has_list(self):
        original_contents = [
            '# KATTIS SOLUTIONS\n',
            'This repository includes my solutions to Kattis problem\n',
            '## Solved Problems\n',
            'line1\n',
            'line2\n'
        ]
        with open(TEST_FILE, 'w') as md_file:
            md_file.writelines(original_contents)
        self.md_list.load_existing_README_contents()
        assert self.md_list.original_contents == original_contents
        assert self.md_list.new_contents == original_contents[:3] + ['<sub><i>Created with [KattisToGithub](https://github.com/Zabrakk/KattisToGithub)</i></sub>\n']

    def test_sort_solved_problems_by_difficulty(self):
        expected_result = ['Hard', 'Medium', 'Easy', 'Easy']
        self.md_list._sort_solved_problems_by_difficulty()
        for i, entry in enumerate(self.md_list.solved_problems):
            assert entry.difficulty == expected_result[i]

    def test_create_solved_problem_list(self):
        solved_problem_list = self.md_list._create_solved_problem_list()
        assert len(solved_problem_list) == 3
        for i, entry in enumerate(solved_problem_list):
            solutions = ' '.join([f'[{language}](Solutions/{filename})' for filename, language in SOLVED_PROBLEMS[i].filename_language_dict.items()])
            expected_result = f'|[{SOLVED_PROBLEMS[i].name}]({SOLVED_PROBLEMS[i].problem_link})|{SOLVED_PROBLEMS[i].difficulty}|' + solutions
            assert entry == expected_result
