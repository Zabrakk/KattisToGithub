from src.solved_problem import SolvedProblem, ProblemStatus

SOLVED_PROBLEMS = [
    SolvedProblem(
        name='Problem1',
        difficulty='Medium',
        status=ProblemStatus.CODE_FOUND,
        problem_link='problem_link1',
        filename_language_dict={'test1.py': 'Python 3', 'test1.cpp': 'C++'}
    ),
    SolvedProblem(
        name='Problem2',
        difficulty='Easy',
        status=ProblemStatus.CODE_FOUND,
        problem_link='problem_link2',
        filename_language_dict={'test2.py': 'Python 3'}
    ),
    SolvedProblem(
        name='Problem3',
        difficulty='Hard',
        status=ProblemStatus.CODE_FOUND,
        problem_link='problem_link3',
        filename_language_dict={'test3.py': 'Python 3'}
    ),
    SolvedProblem(
        name='Problem4',
        difficulty='Easy',
        status=ProblemStatus.CODE_NOT_FOUND,
        problem_link='problem_link4'
    ),
]