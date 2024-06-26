from typing import Dict
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass, field


class ProblemStatus(IntEnum):
    CODE_FOUND = 1
    UPDATE = 0
    CODE_NOT_FOUND = -1


@dataclass
class SolvedProblem:
    problem_link: str = None
    submissions_link: str = None
    name: str = None
    points: str = None
    difficulty: str = None
    status: int = ProblemStatus.CODE_NOT_FOUND
    filename_code_dict: Dict[str, str] = field(default_factory=dict)
    filename_language_dict: Dict[str, str] = field(default_factory=dict)

    def write_to_file(self, directory: Path) -> None:
        for filename in self.filename_code_dict:
            with open(directory / 'Solutions' / filename, 'w') as file:
                file.write(self.filename_code_dict[filename])

    def to_dict(self) -> Dict:
        solutions = '#'.join(['|'.join([language, filename]) for filename, language in self.filename_language_dict.items()])
        return {'Name': self.name, 'Difficulty': self.difficulty, 'Status': self.status.value,
                'ProblemLink': self.problem_link, 'SubmissionsLink': self.submissions_link, 'Solutions': solutions
        }

    def __repr__(self) -> str:
        return \
f'''Problem {self.name}
Link {self.submissions_link}
Points {self.points}
Difficulty {self.difficulty}
Status {self.status._name_}
{self.filename_code_dict}'''
