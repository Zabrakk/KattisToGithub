import os
import sys
import requests
import subprocess
from pathlib import Path
from functools import cached_property
from typing import List, Dict, Generator
from bs4 import BeautifulSoup as Soup
from src.constants import *
from src.csv_handler import CsvHandler
from src.markdown_list import MarkdownList
from src.argument_parser import parse_arguments
from src.solved_problem import SolvedProblem, ProblemStatus


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
        self.no_git = parser.no_git
        self.py_main_only = parser.py_main_only

    def create_folders_for_solutions(self) -> None:
        """
        Creates a folder called Solutions. The code's of solved problems will be stored there
        """
        if not os.path.exists(self.directory / 'Solutions'):
            print(f'#: Creating folder for problem solutions')
            os.mkdir(self.directory / 'Solutions')

    def load_solved_problem_status_csv(self) -> None:
        self.solved_problems = CsvHandler(self.directory).load_solved_problems()

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

    @cached_property
    def _solved_problem_links(self) -> str:
        return [problem.submissions_link for problem in self.solved_problems]

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

    def _get_html(self, url: str) -> Soup:
        response = self.session.get(url)
        return Soup(response.text, 'html.parser')

    def get_solved_problems(self) -> None:
        html = self._get_html(self._solved_problems_url)
        pages = ['']
        for page in pages:
            print(f'#: Collecting solved problems from {self._solved_problems_url + page}')
            html = self._get_html(self._solved_problems_url + page)
            for sp_html in self._find_solved_problems_from_html(html):
                sp = self._parse_solved_problem(sp_html)
                if sp.submissions_link not in self._solved_problem_links:
                    self.solved_problems += [sp]
            self._get_links_to_next_pages(html, pages)
        print(f'#: Found a total of {len(self.solved_problems)} solved problems')

    def _find_solved_problems_from_html(self, html: Soup) -> List[Soup]:
        """
        Extracts entries from the 'problems-tab' of the user's page.

        Returns:
        - List[Soup]: List of table elements containing info on solved problems
        """
        return [solved_problem_html for solved_problem_html in \
            html.find('div', attrs={'id': 'problems-tab'}).find('tbody').find_all('tr')
        ]

    def _get_links_to_next_pages(self, html: Soup, pages: List[str]) -> None:
        """
        Looks for the numbered next page buttons and obtains the query strings from them.

        Parameters:
        - html: BeautifulSoup object created from a HTTP request response.
        - pages: List of query params leading to further pages. The lists contents is updated inside this function.
        """
        next_pages = [href.attrs['href'] for href in html.find_all('a', href=True, attrs={'role': 'button'}) if '?page=' in href.attrs['href']]
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
        problem_link = html.contents[0].find('a')['href']
        return SolvedProblem(
            problem_link=BASE_URL + problem_link,
            submissions_link = self._solved_problem_submission_url + problem_link.replace('/problems/', ''),
            name = html.contents[0].text,
            points = html.contents[4].find('span').text,
            difficulty = html.contents[4].find('span').attrs['class'][-1].split('_')[1].capitalize()
        )

    def get_codes_for_solved_problems(self) -> None:
        print('#: Starting to fetch codes for solved problems')
        ctr = 0
        for solved_problem in self.solved_problems:
            if self._should_look_for_code(solved_problem):
                solved_problem_html = self._get_html(solved_problem.submissions_link)
                for link, language in self._get_submission_link_and_language(solved_problem_html):
                    if language not in solved_problem.filename_language_dict.values():
                        submission_html = self._get_html(link)
                        self._parse_submission(solved_problem, submission_html, language)
                    else:
                        pass
            ctr += 1
            if ctr > 0 and ctr % 59 == 0:
                print(f'#: Checked {ctr} solved problems...')

    def _should_look_for_code(self, solved_problem: SolvedProblem) -> bool:
        return solved_problem.status != ProblemStatus.CODE_FOUND

    def _get_submission_link_and_language(self, html: Soup) -> Generator[str, str, None]:
        for tr in html.find('div', attrs={'id': 'submissions-tab'}).find('tbody').find_all('tr'):
            if tr.find('div', {'class': 'status is-status-accepted'}):
                submission_link = self.base_url + tr.find('td', attrs={'data-type': 'actions'}).find('a', href=True).attrs['href']
                programming_language = tr.find('td', attrs={'data-type': 'lang'}).text
                yield submission_link, programming_language

    def _parse_submission(self, solved_problem: SolvedProblem, html: Soup, language: str) -> bool:
        if len(html.find_all('div', attrs={'class': 'horizontal_link_list'})) > 0:
            print(f'#: CAN\'T DOWNLOAD SUBMISSION FOR {solved_problem.name} BECAUSE THERE IS MORE THAN ONE FILE PRESENT')
            return False
        filename = html.find('div', attrs={'class': 'file_source-content-test'})['data-filename']
        if filename in solved_problem.filename_code_dict:
            return False
        code = html.find(name='div', attrs={'class': 'source-highlight w-full'}).text
        if language == 'Python 3' and not self._python_3_code_is_acceptable(code):
            return False
        self.__add_submission_contents_to_solved_problem(solved_problem, filename, code, language)
        return True

    def _python_3_code_is_acceptable(self, code: str) -> bool:
        if self.py_main_only:
            return 'def main()' in code
        return True

    def __add_submission_contents_to_solved_problem(self, solved_problem: SolvedProblem, filename: str, code: str, lang: str) -> None:
        print(f'#: Loading code for {filename}')
        solved_problem.filename_code_dict[filename] = code
        solved_problem.filename_language_dict[filename] = lang
        solved_problem.status = ProblemStatus.CODE_FOUND
        solved_problem.write_to_file(self.directory)

    def git_add_and_commit_solutions(self) -> None:
        """
        Calls git add on SolvedProblems for which new code was found.
        If there are at most 5 SolvedProblems to commit, each problem gets its own commit message, otherwise only one commit is made.

        Returns:
        - None
        """
        solutions_to_commit = [solved_problem for solved_problem in self.solved_problems if len(solved_problem.filename_code_dict) > 0]
        should_commit_one_by_one = len(solutions_to_commit) < 6
        for solved_problem in solutions_to_commit:
            for filename in solved_problem.filename_code_dict:
                self.__git_add(f'Solutions/{filename}')
                if should_commit_one_by_one:
                    self.__git_commit(f'Solution for {solved_problem.name}')
        if not should_commit_one_by_one:
            self.__git_commit('Added new solutions')

    def __git_add(self, filename: str) -> None:
        if not self.no_git:
            subprocess.Popen(['git', 'add', filename], cwd=self.directory, stdout=subprocess.DEVNULL).wait()

    def __git_commit(self, message: str) -> None:
        if not self.no_git:
            subprocess.Popen(['git', 'commit', f'-m {message}'], cwd=self.directory, stdout=subprocess.DEVNULL).wait()

    def create_markdown_table(self):
        """
        Creates / updates the list of SolvedProblems in README.md

        Returns:
        - None
        """
        md_list = MarkdownList(directory=self.directory, solved_problems=self.solved_problems)
        md_list.create()
        if md_list.should_add_and_commit:
            print('#: Calling git add & commit on README.md')
            self.__git_add(md_list.filename)
            self.__git_commit('Updated README.md')

    def update_status_to_csv(self) -> None:
        """
        Writes the information on SolvedProblems into status.csv

        Returns:
        - None
        """
        self.solved_problems.sort(key=lambda sp: sp.name)
        csv_handler = CsvHandler(self.directory)
        csv_handler.write_solved_problems_to_csv(self.solved_problems)
        if csv_handler.should_add_to_gitignore:
            self.__git_add('status.csv')
            self.__git_commit('Updated .gitignore')


if __name__ == '__main__':
    KTG = KattisToGithub()
    KTG.get_run_details_from_sys_argv()
    KTG.create_folders_for_solutions()
    KTG.load_solved_problem_status_csv()
    if KTG.login():
        KTG.get_solved_problems()
        KTG.get_codes_for_solved_problems()
        KTG.git_add_and_commit_solutions()
        KTG.create_markdown_table()
        KTG.update_status_to_csv()
