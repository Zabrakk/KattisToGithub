import os
import re
import csv
from pathlib import Path
from typing import List
import unittest
import subprocess
from unittest import TestCase, mock
from bs4 import BeautifulSoup as Soup
from src.constants import *
from src.solved_problem import SolvedProblem, ProblemStatus
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


class MockSubprocess:
    def __init__(self, path: Path):
        self.ctr = 0
        self.path = path

    def Popen(self, *args, **kwargs):
        args = args[0]
        assert Path(kwargs['cwd']) == self.path
        assert kwargs['stdout'] == subprocess.DEVNULL
        if args[1] == 'add':
            assert args[2] == 'Solutions/test.py'
            self.ctr += 1
        elif args[1] == 'commit' and self.ctr > 5:
            assert args[2] == '-m Added new solutions'
        elif args[1] == 'commit':
            assert args[2] == '-m Solution for TestSP'
        return self.MockWait()

    class MockWait:
        def wait(self):
            pass


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
        assert KTG.solved_problems == []

    def test_get_run_details_from_sys_argv(self):
        self.KTG.get_run_details_from_sys_argv()
        assert self.KTG.user == USER
        assert self.KTG.password == PASSWORD
        assert self.KTG.directory == Path(__file__).parent
        assert self.KTG.no_git is False
        assert self.KTG.py_main_only is False

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

    def test_load_solved_problem_status_csv_empty_csv(self):
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

    def test_should_look_for_code(self):
        sp = SolvedProblem(status=ProblemStatus.UPDATE)
        assert self.KTG._should_look_for_code(sp) is True
        sp.status = ProblemStatus.CODE_NOT_FOUND
        assert self.KTG._should_look_for_code(sp) is True
        sp.status = ProblemStatus.CODE_FOUND
        assert self.KTG._should_look_for_code(sp) is False

    def test_python_3_code_is_acceptable(self):
        assert self.KTG._python_3_code_is_acceptable('print()') is True
        self.KTG.py_main_only = True
        assert self.KTG._python_3_code_is_acceptable('print()') is False
        assert self.KTG._python_3_code_is_acceptable('def main():print()') is True

    def test_get_submission_link_and_language(self):
        html = """
        <div id="submissions-tab">
            <tbody>
                <tr>
                    <td><div class="status is-status-accepted"></i><span>Accepted</span></div></td>
                    <td data-type="lang">Python 3</td>
                    <td data-type="actions"><a href="/submissions/123">View Details</a></td>
                </tr>
                <tr>
                    <td><div class="status is-status-accepted"></i><span>Accepted</span></div></td>
                    <td data-type="lang">Go</td>
                    <td data-type="actions"><a href="/submissions/124">View Details</a></td>
                </tr>
            </tbody>
        </div>
        """
        html = Soup(re.sub(r'\s\s+', ' ', html), 'html.parser')
        results = self.KTG._get_submission_link_and_language(html)
        assert next(results) == ('https://open.kattis.com/submissions/123', 'Python 3')
        assert next(results) == ('https://open.kattis.com/submissions/124', 'Go')

    def test_parse_submission_more_than_one_file(self):
        html = Soup('<div class="horizontal_link_list ">', 'html.parser')
        assert self.KTG._parse_submission(SolvedProblem(), html, 'Python 3') is False

    def test_parse_submission_same_file_already_found(self):
        sp = SolvedProblem(filename_code_dict={'test.py': 'print()'})
        html = Soup('<div class="file_source-content-test" data-filename="test.py">', 'html.parser')
        assert self.KTG._parse_submission(sp, html, 'Python 3') is False

    def test_parse_submission_python3_accept_main_only(self):
        self.KTG.py_main_only = True
        html = """
        <div class="file_source-content-test" data-filename="test.py">
        <div class="source-highlight w-full">print('Hello')</div>
        """
        html = Soup(re.sub(r'\s\s+', ' ', html), 'html.parser')
        assert self.KTG._parse_submission(SolvedProblem(), html, 'Python 3') is False

    def test_parse_submission(self):
        html = """
        <div class="file_source-content-test" data-filename="test.py">
        <div class="source-highlight w-full">print('Hello')</div>
        """
        html = Soup(re.sub(r'\s\s+', ' ', html), 'html.parser')
        sp = SolvedProblem()
        with mock.patch('src.solved_problem.SolvedProblem.write_to_file', return_value=None):
            assert self.KTG._parse_submission(sp, html, 'Python 3') is True
            assert sp.filename_code_dict == {'test.py': "print('Hello')"}
            assert sp.filename_language_dict == {'test.py': 'Python 3'}
            assert sp.status == ProblemStatus.CODE_FOUND

    @use_test_credentials
    def test_get_codes_for_solved_problems(self):
        self.KTG.py_main_only = False
        self.KTG.login()
        with mock.patch('KattisToGithub.KattisToGithub._get_links_to_next_pages', return_value=[]):
            self.KTG.get_solved_problems()
        self.KTG.solved_problems = self.KTG.solved_problems[:3]
        with mock.patch('src.solved_problem.SolvedProblem.write_to_file', return_value=None):
            self.KTG.get_codes_for_solved_problems()
            for sp in self.KTG.solved_problems:
                assert sp.status in [ProblemStatus.CODE_FOUND, ProblemStatus.CODE_NOT_FOUND]
                if sp.status == ProblemStatus.CODE_FOUND:
                    assert len(sp.filename_code_dict) > 0
                    assert len(sp.filename_language_dict) > 0

    def test_git_add_and_commit_solution_5_solutions(self):
        self.KTG.solved_problems = [SolvedProblem(
            name='TestSP', filename_code_dict={'test.py': 'print("Hello")'}
        )] * 5
        ms = MockSubprocess(self.KTG.directory)
        with mock.patch('subprocess.Popen', ms.Popen):
            self.KTG.git_add_and_commit_solutions()
        assert self.KTG.user_should_git_push is True

    def test_git_add_and_commit_solution_mote_than_5_solutions(self):
        self.KTG.solved_problems = [SolvedProblem(
            name='TestSP', filename_code_dict={'test.py': 'print("Hello")'}
        )] * 6
        ms = MockSubprocess(self.KTG.directory)
        with mock.patch('subprocess.Popen', ms.Popen):
            self.KTG.git_add_and_commit_solutions()

    def test_git_add_and_commit_solution_no_git(self):
        self.KTG.no_git = True
        self.KTG.solved_problems = [SolvedProblem(
            name='TestSP', filename_code_dict={'test.py': 'print("Hello")'}
        )] * 5
        ms = MockSubprocess(self.KTG.directory)
        with mock.patch('subprocess.Popen', ms.Popen):
            self.KTG.git_add_and_commit_solutions()
        assert ms.ctr == 0

    def test_create_markdown_table(self):
        self.KTG.no_git = True
        self.KTG.solved_problems = [
            SolvedProblem(name='A', problem_link='B', difficulty='Easy', filename_language_dict={'D': 'E'})
        ]
        self.KTG.create_markdown_table()
        assert os.path.exists('test/README.md')
        os.remove('test/README.md')

    def test_create_markdown_table_when_no_readme_is_true(self):
        self.KTG.no_readme = True
        self.KTG.solved_problems = [
            SolvedProblem(name='A', problem_link='B', difficulty='Easy', filename_language_dict={'D': 'E'})
        ]
        self.KTG.create_markdown_table()
        assert not os.path.exists('test/README.md')

    def test_update_status_to_csv(self):
        self.KTG.no_git = True
        self.KTG.solved_problems = [
            SolvedProblem(name='A', problem_link='B', difficulty='Easy', filename_language_dict={'D': 'E'})
        ]
        self.KTG.update_status_to_csv()
        assert os.path.exists('test/status.csv')
        os.remove('test/status.csv')
