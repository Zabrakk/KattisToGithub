import os
import csv
from pathlib import Path
import unittest
from unittest import TestCase
from src.csv_handler import CsvHandler
from src.solved_problem import SolvedProblem
from src.constants import CSV_FIELD_NAMES
from constants import SOLVED_PROBLEMS, TEST_DIR

TEST_FILE = TEST_DIR + '/status.csv'


class TestCsvHandler(TestCase):
    def setUp(self) -> None:
        self.csv_hadler = CsvHandler(directory=Path(TEST_DIR))
        return super().setUp()
    
    def tearDown(self) -> None:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        return super().tearDown()

    def test_load_solved_problems_no_csv_file(self):
        assert self.csv_hadler.load_solved_problems() == []

    def test_load_solved_problems_csv_file_empty(self):
        with open(TEST_FILE, 'w') as _:
            pass
        assert self.csv_hadler.load_solved_problems() == []

    def test_load_solved_problems_incorrect_problem_status(self):
        with open(TEST_FILE, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES[:3])
            writer.writeheader()
            writer.writerow({
                'Name': 'Test', 'Difficulty': 'Easy', 'Status': -2
            })
        assert self.csv_hadler.load_solved_problems() == []

    def test_load_solved_problems_info_missing(self):
        with open(TEST_FILE, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES[:3])
            writer.writeheader()
            writer.writerow({
                'Name': 'Test', 'Difficulty': 'Easy', 'Status': -1
            })
        assert self.csv_hadler.load_solved_problems() == []

    def test_load_solved_problems(self):
        with open(TEST_FILE, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES)
            writer.writeheader()
            writer.writerow(SOLVED_PROBLEMS[0].to_dict())
        assert self.csv_hadler.load_solved_problems() == [SOLVED_PROBLEMS[0]]

    def test_write_solved_problems_to_csv(self):
        self.csv_hadler.write_solved_problems_to_csv(SOLVED_PROBLEMS)
        assert self.csv_hadler.load_solved_problems() == SOLVED_PROBLEMS
