import os
import sys
from pathlib import Path
import requests
from functools import cached_property
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
        self.solved_problems: List[SolvedProblem] = []

    def get_run_details_from_sys_argv(self) -> None:
        """
        Uses src/argument_parser to extract the Kattis login details from command line input.
        Stores these values to self.user and self.password respectively.
        """
        parser = parse_arguments(sys.argv[1:])
        self.user = parser.user
        self.password = parser.password
        self.directory = Path(__file__).parent / parser.directory

    def create_folders_for_different_difficulties(self) -> None:
        """
        Creates a folder for each of the different problem difficulties if they don't already exist
        """
        for difficulty in ['Easy', 'Medium', 'Hard']:
            if not os.path.exists(self.directory / difficulty):
                print(f'#: Creating folder for {difficulty} problem solutions')
                os.mkdir(self.directory / difficulty)

    @property
    def login_payload(self) -> Dict:
        return {
            'csrf_token': self._get_CSRF_token(),
            'user': self.user,
            'password': self.password
        }

    @cached_property
    def _solved_problems_url(self) -> str:
        return f'{self.base_url}/users/{self.user}'

    @cached_property
    def _solved_problem_submission_url(self) -> str:
        return f'{self._solved_problems_url}?tab=submissions&problem='

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
        print('#: Attempting to login')
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
        response = self.session.get(self._solved_problems_url)
        html = Soup(response.text, 'html.parser')
        pages = ['']
        self._get_links_to_next_pages(html, pages)
        for page in pages:
            print(f'#: Collecting solved problems from {self._solved_problems_url + page}')
            response = self.session.get(self._solved_problems_url + page)
            html = Soup(response.text, 'html.parser')
            for tr in html.find_all('tr'):
                if len(tr.contents) == 6 and 'difficulty_number' in tr.contents[4].find('span').attrs['class']:
                    self.solved_problems += [self._parse_solved_problem(tr)]
            self._get_links_to_next_pages(html, pages)
        print(f'#: Found a total of {len(self.solved_problems)} solved problems')

    def _get_links_to_next_pages(self, html: Soup, pages: List[str]) -> List[str]:
        """
        Looks for the numbered next page buttons and obtains the query strings from them.

        Parameters:
        - html: BeautifulSoup object created from a HTTP request response.
        - pages: List of query params leading to further pages. The lists contents is updated inside this function.

        Returns:
        - List[str]: Updated list of query strings without duplicates or the page number 1.
        """
        next_pages = [href.attrs['href'] for href in html.find_all('a', href=True) if '?page=' in href.attrs['href']]
        for next_page in next_pages:
            if next_page not in pages and next_page != '?page=1':
                pages += [next_page]

    def _parse_solved_problem(self, html) -> SolvedProblem:
        """
        Creates a SolvedProblem object based on given data

        Parameters:
        - html: BeautifulSoup object created from a HTTP request response.

        Returns:
        - SolvedProblem
        """
        return SolvedProblem(
            link = self._solved_problem_submission_url + html.contents[0].find('a')['href'].replace('/problems/', ''),
            name = html.contents[0].text,
            points = html.contents[4].find('span').text,
            difficulty = html.contents[4].find('span').attrs['class'][-1].split('_')[1].capitalize()
        )

    def get_codes_for_solved_problems(self):
        print('#: Starting to fetch codes for solved problems')
        i = 0
        for solved_problem in self.solved_problems:
            response = self.session.get(solved_problem.link)
            solved_problem_html = Soup(response.text, 'html.parser')
            # Obtain links to submissions
            for tag in solved_problem_html.find_all(lambda tag: 'data-submission-id' in tag.attrs):
                if tag.find('div', {'class': 'status is-status-accepted'}):
                    link = self.base_url + tag.contents[-1].find('a', href=True).attrs['href']
                    response = self.session.get(link)
                    submission_html = Soup(response.text, 'html.parser')
                    print(link)
                    if submission_html.find('td', {'data-type': 'lang'}).text == 'Python 3':
                        solved_problem.file_name = submission_html.find('span', attrs={'class': 'mt-2'}).code.text
                        code = submission_html.find(name='div', attrs={'class': 'source-highlight w-full'}).text
                        if 'def main():' in code:
                            solved_problem.code += [code]
                            print(solved_problem)
                            break
            i += 1
            if i > 10:
                break


if __name__ == '__main__':
    KTG = KattisToGithub()
    KTG.get_run_details_from_sys_argv()
    KTG.create_folders_for_different_difficulties()
    if KTG.login():
        KTG.get_solved_problems()
        KTG.get_codes_for_solved_problems()
