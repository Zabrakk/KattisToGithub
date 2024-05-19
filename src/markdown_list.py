import os
from typing import List
from pathlib import Path
from src.solved_problem import SolvedProblem, ProblemStatus


class MarkdownList:
    def __init__(self, directory: Path, solved_problems: List[SolvedProblem]) -> None:
        self.__filepath = directory / 'README.md'
        self.__solved_problems = solved_problems

    @property
    def solved_problems(self) -> List[SolvedProblem]:
        return self.__solved_problems

    @property
    def original_contents(self) -> List[str]:
        return self.__original_contents

    @property
    def new_contents(self) -> List[str]:
        return self.__new_contents

    def load_existing_README_contents(self) -> None:
        if os.path.exists(self.__filepath):
            with open(self.__filepath, 'r') as md_file:
                self.__original_contents = md_file.readlines()
                self.__new_contents = self.__parse_loaded_README(self.__original_contents)
        else:
            self.__original_contents = []
            self.__new_contents = []

    def __parse_loaded_README(self, contents: List[str]) -> List[str]:
        try:
            new_contents = contents[:contents.index('## Solved Problems\n')]
        except ValueError:
            new_contents = contents + ['\n']
        new_contents += ['## Solved Problems\n']
        return new_contents + ['<sub><i>Created with [KattisToGithub](https://github.com/Zabrakk/KattisToGithub)</i></sub>\n']

    def _sort_solved_problems_by_difficulty(self) -> List[SolvedProblem]:
        order = ['Hard', 'Medium', 'Easy']
        self.__solved_problems.sort(key=lambda sp: order.index(sp.difficulty))

    def _create_solved_problem_list(self) -> List[str]:
        return [
            f'|[{sp.name}]({sp.problem_link})|{sp.difficulty}|' + self.__create_solutions_tab_content_for_solved_problem(sp)\
            for sp in self.__solved_problems if sp.status != ProblemStatus.CODE_NOT_FOUND
        ]

    def __create_solutions_tab_content_for_solved_problem(self, solved_problem: SolvedProblem) -> str:
        return ' '.join([f'[{language}](Solutions/{filename})' for filename, language in solved_problem.filename_language_dict.items()])

    def _save_contents_to_README(self, contetns: List[str]) -> None:
        pass
        #with op

    def create(self):
        pass