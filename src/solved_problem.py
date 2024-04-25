from pathlib import Path
from dataclasses import dataclass


@dataclass
class SolvedProblem:
    link: str = None
    name: str = None
    file_name: str = None
    points: str = None
    difficulty: str = None
    code = []

    def write_to_file(self, directory: Path) -> None:
        # TODO: Expand to write multiple files if different languages found
        with open(directory / self.difficulty / self.file_name, 'w') as file:
            file.write(self.code[0])

    def __repr__(self) -> str:
        return \
f'''Problem {self.name}
filename {self.file_name}
link {self.link}
points {self.points}
Difficulty {self.difficulty}
{self.code}'''
