from typing import List
from unittest import TestCase, mock
from src.constants import *
from KattisToGithub import KattisToGithub

CSRF_TOKEN = '12345'
USER = 'my_username'
PASSWORD = 'my_password'
DIRECTORY = 'tests'


class MockPost:
    def __init__(self, *args, **kwargs) -> None:
        pass
    status_code = 200
    url = BASE_URL


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
                return {'href': 'CorrectLink'}
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
        self.csrf_token_mock = mock.patch('KattisToGithub.KattisToGithub._get_CSRF_token', return_value=CSRF_TOKEN)
        self.csrf_token_mock.start()
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
        assert self.KTG.directory == DIRECTORY

    def test_get_CSRF_token(self):
        self.csrf_token_mock.stop()
        token = self.KTG._get_CSRF_token()
        assert token.isnumeric()

    def test_login_payload_property(self):
        assert self.KTG.login_payload == {
            'csrf_token': CSRF_TOKEN,
            'user': USER,
            'password': PASSWORD
        }

    def test_solved_problems_url_property(self):
        assert self.KTG._solved_problems_url == f'{BASE_URL}/users/{USER}'

    def test_login_fail(self):
        assert not self.KTG.login()

    def test_login_success(self):
        with mock.patch('requests.sessions.Session.post', MockPost):
            assert self.KTG.login()

    def test_get_solved_problems(self):
        # TODO
        assert False

    def test_get_links_to_next_pages(self):
        pages = []
        self.KTG._get_links_to_next_pages(MockSoup(), pages=pages)
        assert pages == ['?page=2', '?page=3']
        # Check that duplicates are not added
        self.KTG._get_links_to_next_pages(MockSoup(), pages=pages)
        assert pages == ['?page=2', '?page=3']

    def test_parse_solved_problem(self):
        sp = self.KTG._parse_solved_problem(MockSoup())
        assert sp.link == 'CorrectLink'
        assert sp.name == 'ProblemName'
        assert sp.points == '3.0'
        assert sp.difficulty == 'Medium'
