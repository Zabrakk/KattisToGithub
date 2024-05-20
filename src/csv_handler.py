import os
import csv
from pathlib import Path
from typing import List, Dict
from src.constants import CSV_FIELD_NAMES
from src.solved_problem import SolvedProblem, ProblemStatus


class CsvHandler:
    def __init__(self, directory: Path) -> None:
        self.__filepath = directory / 'status.csv'

    @property
    def filepath(self) -> Path:
        return self.__filepath

    def load_solved_problems(self) -> List[SolvedProblem]:
        if not os.path.exists(self.__filepath):
            return []
        solved_problems = []
        try:
            with open(self.__filepath, 'r') as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=CSV_FIELD_NAMES)
                reader.__next__()
                for row in reader:
                    solved_problems += [self.__load_solved_problem_from_csv_row(row)]
        except StopIteration:
            print('#: Status.csv was empty')
        except ValueError as e:
            print(f'#: Incorrect entry in status.csv\n{e}')
        return solved_problems

    def __load_solved_problem_from_csv_row(self, row: Dict) -> SolvedProblem:
       return SolvedProblem(
            name=self.__ensure_not_None(row['Name']),
            difficulty=self.__ensure_not_None(row['Difficulty']),
            status=ProblemStatus(int(self.__ensure_not_None(row['Status']))),
            problem_link=self.__ensure_not_None(row['ProblemLink']),
            submissions_link=self.__ensure_not_None(row['SubmissionsLink']),
            filename_language_dict=self.__build_filename_language_dict_from_str(row['Solutions'])
        )

    def __build_filename_language_dict_from_str(self, val: str) -> Dict:
        filename_language_dict = {}
        try:
            for entry in val.split('#'):
                language, filename = entry.split('|')
                filename_language_dict[filename] = language
        except ValueError as e:
            pass
        return filename_language_dict

    def __ensure_not_None(self, val: any) -> any:
        if val is not None:
            return val
        raise ValueError('None value in csv')

    def write_solved_problems_to_csv(self, solved_problems: List[SolvedProblem]) -> None:
        with open(self.__filepath, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES)
            writer.writeheader()
            for solved_problem in solved_problems:
                writer.writerow(solved_problem.to_dict())
