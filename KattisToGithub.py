import sys
import requests
from typing import List, Dict
from bs4 import BeautifulSoup as Soup
from src.constants import *
from src.argument_parser import parse_arguments
from src.solved_problem import SolvedProblem


class KattisToGithub:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.base_url = BASE_URL
        self.login_url = LOGIN_URL
        self.problems: List[SolvedProblem]

    def get_run_details_from_sys_argv(self) -> None:
        """
        Uses src/argument_parser to extract the Kattis login details from command line input.
        Stores these values to self.user and self.password respectively.
        """
        parser = parse_arguments(sys.argv[1:])
        self.user = parser.user
        self.password = parser.password
        self.directory = parser.directory

    @property
    def login_payload(self) -> Dict:
        return {
            'csrf_token': self._get_CSRF_token(),
            'user': self.user,
            'password': self.password
        }

    @property
    def _solved_problems_url(self) -> str:
        return f'{self.base_url}/users/{self.user}'

    def _get_CSRF_token(self) -> str:
        """
        Obtains the sessions CSRF token from the login page.

        Returns:
        - str: CSRF token
        """
        response = self.session.get(self.login_url)
        if response.status_code != 200:
            print('#: GETin the login page failed')
            return
        soup = Soup(response.text, 'html.parser')
        return soup.find('input', {'name': 'csrf_token'}).get('value')


    def login(self) -> bool:
        """
        Logs into Kattis with the given credentials.

        Returns:
        - bool: True if successfully logged in; False otherwise
        """
        response = self.session.post(self.login_url, data=self.login_payload, timeout=30)
        if response.status_code != 200:
            print('#: Something went wrong during login')
            return False
        if response.url == self.login_url:
            print(f'#: Login failed')
            return False
        else:
            print('#: Logged in to Kattis')
            return True

    def get_solved_problems(self) -> None:
        # TODO
        response = self.session.get(self._solved_problems_url)
        soup = Soup(response.text, 'html.parser')
        for tr in soup.find_all('tr'):
            if len(tr.contents) == 6 and 'difficulty_number' in tr.contents[4].find('span').attrs['class']:
                self._parse_solved_problem(tr)
                break

    def _parse_solved_problem(self, html):
        sp = SolvedProblem(
            link = html.contents[0].find('a')['href'],
            name = html.contents[0].text,
            points = html.contents[4].find('span').text,
            difficulty = html.contents[4].find('span').attrs['class'][-1].split('_')[1].capitalize()
        )
        print(sp)


if __name__ == '__main__':
    KTG = KattisToGithub()
    KTG.get_run_details_from_sys_argv()
    if KTG.login():
        KTG.get_solved_problems()
