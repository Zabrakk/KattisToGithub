from typing import Dict
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass


class ProblemStatus(IntEnum):
    CODE_FOUND = 1
    UPDATE = 0
    CODE_NOT_FOUND = -1


@dataclass
class SolvedProblem:
    link: str = None
    name: str = None
    points: str = None
    difficulty: str = None
    status: int = ProblemStatus.CODE_NOT_FOUND
    filename_code_dict = {}

    def write_to_file(self, directory: Path) -> None:
        # TODO: Expand to write multiple files if different languages found
        for filename in self.filename_code_dict:
            with open(directory / self.difficulty / filename, 'w') as file:
                file.write(self.filename_code_dict[filename])

    def to_dict(self) -> Dict:
        return {'Name': self.name, 'Difficulty': self.difficulty, 'Status': self.status.value, 'Link': self.link}

    def __repr__(self) -> str:
        return \
f'''Problem {self.name}
Link {self.link}
Points {self.points}
Difficulty {self.difficulty}
Status {self.status._name_}
{self.filename_code_dict}'''
