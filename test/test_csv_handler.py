from pathlib import Path
import unittest
from unittest import TestCase
from src.csv_handler import CsvHandler
from src.solved_problem import SolvedProblem
from src.constants import CSV_FIELD_NAMES

TEST_FILE = Path('test/status.csv')


class TestCsvHandler(TestCase):
    def setUp(self) -> None:
        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()
    
    def test_create(self):
        assert CsvHandler(directory=TEST_FILE)

    @unittest.skip(reason='TODO')
    def test_load_solvd_problems(self):
        pass

    @unittest.skip(reason='TODO')
    def test_write_solved_problems_to_csv(self):
        pass
