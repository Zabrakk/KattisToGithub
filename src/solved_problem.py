from typing import List
from dataclasses import dataclass


@dataclass
class SolvedProblem:
    link: str = None
    name: str = None
    points: str = None
    difficulty: str = None
    code: str = None

    def __repr__(self) -> str:
        return f'''
Problem {self.name}
link {self.link}
points {self.points}
Difficulty {self.difficulty}
{self.code}'''
