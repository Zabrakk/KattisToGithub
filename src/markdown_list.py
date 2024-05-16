import os
from typing import List
from pathlib import Path
from src.solved_problem import SolvedProblem, ProblemStatus


class MarkdownList:
    def __init__(self, directory: Path, solved_problems: List[SolvedProblem]) -> None:
        self._filepath = directory / 'README.md'
        self._solved_problems = solved_problems

    def load_existing_README_contents(self) -> None:
        if os.path.exists(self._filepath):
            with open(self._filepath, 'r') as md_file:
                self.original_contents = md_file.readlines()
        else:
            self.original_contents = []

    def _sort_solved_problems_by_difficulty(self) -> List[SolvedProblem]:
        order = ['Hard', 'Medium', 'Easy']
        self._solved_problems.sort(key=lambda sp: order.index(sp.difficulty))

    def __create_solutions_tab_content_for_solved_problem(self, solved_problem: SolvedProblem) -> str:
        return ' '.join([f'[{language}](Solutions/{filename})' for filename, language in solved_problem.filename_language_dict.items()])

    def _create_solved_problem_list(self) -> None:
        self.solved_problem_list = [
            f'|[{sp.name}]({sp.problem_link})|{sp.difficulty}|' + self.__create_solutions_tab_content_for_solved_problem(sp)\
            for sp in self._solved_problems if sp.status != ProblemStatus.CODE_NOT_FOUND
        ]

    def create(self):
        pass