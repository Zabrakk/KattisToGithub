from dataclasses import dataclass


@dataclass
class SolvedProblem:
    link: str = None
    name: str = None
    file_name: str = None
    points: str = None
    difficulty: str = None
    code = []

    def __repr__(self) -> str:
        return f'''
Problem {self.name}
filename {self.file_name}
link {self.link}
points {self.points}
Difficulty {self.difficulty}
{self.code}'''
