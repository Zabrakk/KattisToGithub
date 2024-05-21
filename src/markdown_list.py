import os
from typing import List
from pathlib import Path
from copy import deepcopy
from src.constants import README_LIST_TITLE, KTG_AD, README_LIST_COLUMN_TITLES, README_LIST_POSITIONING
from src.solved_problem import SolvedProblem, ProblemStatus


class MarkdownList:
    """
    MarkdownList is used to automatically create / update the README.md with a list of solved problems.

    Parameters:
    - directory: A Path object pointing to the location where the README.md file should be created.
    - solved_problems: A list of SolvedProblem objects. The list is created based on these.
    """
    def __init__(self, directory: Path, solved_problems: List[SolvedProblem]) -> None:
        self.__filepath = directory / 'README.md'
        self.__solved_problems = deepcopy(solved_problems)

    @property
    def solved_problems(self) -> List[SolvedProblem]:
        return self.__solved_problems

    @property
    def original_contents(self) -> List[str]:
        return self.__original_contents

    @property
    def new_contents(self) -> List[str]:
        return self.__new_contents

    @property
    def should_add_and_commit(self) -> bool:
        """
        If true, the created README.md file should be added and commited with Git.
        """
        return self.__new_contents != self.__original_contents

    @property
    def filepath(self) -> Path:
        return self.__filepath

    def _load_existing_README_contents(self) -> None:
        """
        Loads the contents of a README.md which might already exist.
        The contents is then appended with KattisToGithub info.

        Returns:
        - None
        """
        if os.path.exists(self.__filepath):
            with open(self.__filepath, 'r', encoding='utf-8') as md_file:
                self.__original_contents = md_file.readlines()
        else:
            self.__original_contents = []
        self.__new_contents = self.__parse_loaded_README(self.__original_contents)

    def __parse_loaded_README(self, contents: List[str]) -> List[str]:
        try:
            new_contents = contents[:contents.index(README_LIST_TITLE)]
        except ValueError:
            new_contents = contents + ['\n']
        new_contents += [README_LIST_TITLE, KTG_AD, README_LIST_COLUMN_TITLES, README_LIST_POSITIONING]
        return new_contents

    def _sort_solved_problems_by_difficulty(self) -> None:
        """
        Sorts the MarkdownList's SolvedProblem list by difficulty.
        Once sorted, Hard difficulty SolvedProblems are first in the list, Easy problems are at the end, and Medium in the middle.

        Returns:
        - None
        """
        order = ['Hard', 'Medium', 'Easy']
        self.__solved_problems.sort(key=lambda sp: order.index(sp.difficulty))

    def _create_solved_problem_list(self) -> List[str]:
        """
        Create a list of strings based on the SolvedProblems which don't have the status CODE_NOT_FOUND. The strings follow the format:
        |[Problem name](link to problem) | Problem difficulty | [Solution programming language](link to solution)|

        Returns:
        - List[str]: Markdown list of SolvedProblems
        """
        return [
            f'|[{sp.name}]({sp.problem_link})|{sp.difficulty}|' + self.__create_solutions_tab_content_for_solved_problem(sp) + '\n' \
            for sp in self.__solved_problems if sp.status != ProblemStatus.CODE_NOT_FOUND
        ]

    def __create_solutions_tab_content_for_solved_problem(self, solved_problem: SolvedProblem) -> str:
        return ' '.join([f'[{language}](Solutions/{filename})' for filename, language in solved_problem.filename_language_dict.items()])

    def _save_contents_to_README(self, contents: List[str]) -> None:
        """
        Saves the contents, given as a paramter, into README.md.

        Parameters:
        - contents: List of strings which will be written into the README.md file

        Returns:
        - None
        """
        with open(self.__filepath, 'w', encoding='utf-8') as md_file:
            md_file.writelines(contents)

    def create(self) -> None:
        """
        Creates and saves the README.md made by KattisToGithub

        Returns:
        - None
        """
        self._load_existing_README_contents()
        self._sort_solved_problems_by_difficulty()
        self.__new_contents += self._create_solved_problem_list()
        self._save_contents_to_README(self.__new_contents)
