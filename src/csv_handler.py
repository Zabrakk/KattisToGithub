import csv
from typing import List
from pathlib import Path
from src.constants import CSV_FIELD_NAMES
from src.solved_problem import SolvedProblem


class CsvHandler:
    def __init__(self, directory: Path) -> None:
        self.__filepath = directory / 'status.csv'

    @property
    def filepath(self) -> Path:
        return self.__filepath
    
    def load_solved_problems(self) -> List[SolvedProblem]:
        # TODO
        pass

    def write_solved_problems_to_csv(self, solved_problems: List[SolvedProblem]) -> None:
        # TODO
        pass
