import os
import csv
from pathlib import Path
from typing import List
import unittest
from unittest import TestCase, mock
from src.constants import *
from KattisToGithub import KattisToGithub

CSRF_TOKEN = '12345'
USER = 'my_username'
PASSWORD = 'my_password'
DIRECTORY = 'test'

try:
    with open('test/test_credentials.txt', 'r') as f:
        TEST_CREDENTIALS = list(map(str.strip, f.readlines()))
except:
    TEST_CREDENTIALS = []


def use_test_credentials(func):
    def wrapper(*args):
        print(TEST_CREDENTIALS)
        if len(TEST_CREDENTIALS) != 2:
            raise unittest.SkipTest('test/test_credentials.txt is empty')
        args[0].KTG.user = TEST_CREDENTIALS[0]
        args[0].KTG.password = TEST_CREDENTIALS[1]
        return func(*args)
    return wrapper


class MockSoup:
    class NextPageHref:
        def __init__(self, page_num: int) -> None:
            self.attrs = {'href': f'?page={page_num}'}

    class SolvedProblemTr:
        def __init__(self, text='ProblemName') -> None:
            self.text = text
            self.attrs = {'class': ['', 0, 0, 'difficulty_medium']}

        def find(self, arg):
            if arg == 'a':
                return {'href': '/problems/CorrectLink'}
            elif arg == 'span':
                self.text = '3.0'
                return self

    @property
    def contents(self) -> List:
        return [MockSoup.SolvedProblemTr(), None, None, None, MockSoup.SolvedProblemTr()]

    def find_all(*args, **kwargs) -> List:
        return [MockSoup.NextPageHref(page_num=i) for i in range(1, 4)]



class TestKattisToGithub(TestCase):
    def setUp(self) -> None:
        mock.patch('sys.argv', ['', '-u', USER, '-p', PASSWORD, '-d', DIRECTORY]).start()
        self.KTG = KattisToGithub()
        self.KTG.get_run_details_from_sys_argv()
        return super().setUp()

    def tearDown(self) -> None:
        mock.patch.stopall()
        return super().tearDown()

    def test_create(self):
        KTG = KattisToGithub()
        assert KTG.session
        assert KTG.base_url == BASE_URL
        assert KTG.login_url == LOGIN_URL

    def test_get_run_details_from_sys_argv(self):
        self.KTG.get_run_details_from_sys_argv()
        assert self.KTG.user == USER
        assert self.KTG.password == PASSWORD
        assert self.KTG.directory == Path(__file__).parent

    def test_create_folders_for_solutions(self):
        self.KTG.create_folders_for_solutions()
        assert os.path.exists('test/Solutions')
        os.rmdir('test/Solutions')

    def test_load_solved_problem_status_csv(self):
        with open('test/status.csv', 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES)
            writer.writeheader()
            writer.writerow({'Name': 'Test', 'Difficulty': 'Easy', 'Status': 1,'ProblemLink': 'problem_link',
                             'SubmissionsLink': 'submissions-link', 'Solutions': 'Python 3|test.py#C++|test.cpp'})
        self.KTG.load_solved_problem_status_csv()
        assert len(self.KTG.solved_problems) == 1
        sp = self.KTG.solved_problems[0]
        assert sp.name == 'Test'
        assert sp.difficulty == 'Easy'
        assert sp.status == 1
        assert sp.problem_link == 'problem_link'
        assert sp.submissions_link == 'submissions-link'
        assert sp.filename_language_dict == {'test.py': 'Python 3', 'test.cpp': 'C++'}
        os.remove('test/status.csv')

    def test_load_solved_problem_status_csv_no_status_csv(self):
        self.KTG.load_solved_problem_status_csv()
        assert self.KTG.solved_problems == []

    def test_load_solved_problem_status_csv_empy_csv(self):
        with open('test/status.csv', 'w', newline='') as _:
            pass
        assert self.KTG.load_solved_problem_status_csv() is None
        os.remove('test/status.csv')

    def test_get_CSRF_token(self):
        token = self.KTG._get_CSRF_token()
        assert token.isnumeric()

    def test_login_payload_property(self):
        with  mock.patch('KattisToGithub.KattisToGithub._get_CSRF_token', return_value=CSRF_TOKEN):
            assert self.KTG.login_payload == {
                'csrf_token': CSRF_TOKEN,
                'user': USER,
                'password': PASSWORD
            }

    def test_solved_problems_url_property(self):
        assert self.KTG._solved_problems_url == f'{BASE_URL}/users/{USER}'

    def test_login_fail(self):
        assert not self.KTG.login()

    @use_test_credentials
    def test_login_success(self):
        assert self.KTG.login()

    @unittest.skip(reason='TODO')
    def test_get_solved_problems_mocked(self):
        with mock.patch('KattisToGithub.KattisToGithub._get_html', return_value=None):
            pass

    @use_test_credentials
    def test_get_solved_problems(self):
        self.KTG.login()
        assert self.KTG.get_solved_problems() is None
        assert len(self.KTG.solved_problems) > 0

    def test_get_links_to_next_pages(self):
        pages = []
        self.KTG._get_links_to_next_pages(MockSoup(), pages=pages)
        assert pages == ['?page=2', '?page=3']
        # Check that duplicates are not added
        self.KTG._get_links_to_next_pages(MockSoup(), pages=pages)
        assert pages == ['?page=2', '?page=3']

    def test_parse_solved_problem(self):
        sp = self.KTG._parse_solved_problem(MockSoup())
        assert sp.submissions_link == f'https://open.kattis.com/users/{USER}?tab=submissions&problem=CorrectLink'
        assert sp.name == 'ProblemName'
        assert sp.points == '3.0'
        assert sp.difficulty == 'Medium'

    @unittest.skipIf(TEST_CREDENTIALS is None, reason='No test credentials given')
    def test_fail(self):
        print(TEST_CREDENTIALS)
        assert True
