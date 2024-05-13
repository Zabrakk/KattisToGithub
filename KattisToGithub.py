import os
import sys
import csv
from pathlib import Path
import requests
from functools import cached_property
from typing import List, Dict
from bs4 import BeautifulSoup as Soup
from src.constants import *
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
        self.update = parser.update

    def create_folders_for_different_difficulties(self) -> None:
        """
        Creates a folder for each of the different problem difficulties if they don't already exist
        """
        for difficulty in ['Easy', 'Medium', 'Hard']:
            if not os.path.exists(self.directory / difficulty):
                print(f'#: Creating folder for {difficulty} problem solutions')
                os.mkdir(self.directory / difficulty)

    def load_solved_problem_status_csv(self) -> None:
        if os.path.exists(self.directory / 'status.csv'):
            with open(self.directory / 'status.csv', 'r') as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=CSV_FIELD_NAMES)
                reader.__next__()
                for row in reader:
                    self.solved_problems += [self._load_solved_problem_from_csv_row(row)]

    def _load_solved_problem_from_csv_row(self, row: Dict) -> SolvedProblem:
        return SolvedProblem(
            name=row['Name'],
            difficulty=row['Difficulty'],
            status=ProblemStatus(int(row['Status'])),
            link=row['Link']
        )

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
    def _solved_problem_names(self) -> str:
        return [problem.name for problem in self.solved_problems]

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
        self._get_links_to_next_pages(html, pages)
        for page in pages:
            print(f'#: Collecting solved problems from {self._solved_problems_url + page}')
            html = self._get_html(self._solved_problems_url + page)
            for tr in html.find_all('tr'):
                if len(tr.contents) == 6 and 'difficulty_number' in tr.contents[4].find('span').attrs['class']:
                    sp = self._parse_solved_problem(tr)
                    if sp.name not in self._solved_problem_names:
                        self.solved_problems += [sp]
                    else:
                        existing_entry = [problem for problem in self.solved_problems if problem.name == sp.name][0]
                        existing_entry.link = sp.link
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

    def get_codes_for_solved_problems(self) -> None:
        print('#: Starting to fetch codes for solved problems')
        i = 0
        for solved_problem in self.solved_problems:
            if self.update and solved_problem.status != ProblemStatus.UPDATE:
                print(f'#: Skipping {solved_problem.name}, status != UPDATE')
                continue
            if solved_problem.status == 1:
                print(f'#: Not updating solution for {solved_problem.name}')
                continue
            solved_problem_html = self._get_html(solved_problem.link)
            # Obtain links to submissions
            for tag in solved_problem_html.find_all(lambda tag: 'data-submission-id' in tag.attrs):
                if tag.find('div', {'class': 'status is-status-accepted'}):
                    link = self.base_url + tag.contents[-1].find('a', href=True).attrs['href']
                    submission_html = self._get_html(link)
                    print(link)
                    if submission_html.find('td', {'data-type': 'lang'}).text == 'Python 3':
                        filename = submission_html.find('span', attrs={'class': 'mt-2'}).code.text
                        code = submission_html.find(name='div', attrs={'class': 'source-highlight w-full'}).text
                        if 'def main():' in code:
                            solved_problem.filename_code_dict[filename] = code
                            solved_problem.status = ProblemStatus.CODE_FOUND
                            print(solved_problem)
                            solved_problem.write_to_file(self.directory)
                            break
                        else:
                            solved_problem.status = ProblemStatus.CODE_NOT_FOUND
            i += 1
            if i > 3:
                break

    def update_status_to_csv(self) -> None:
        with open(self.directory / 'status.csv', 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES)
            writer.writeheader()
            for solved_problem in self.solved_problems:
                writer.writerow(solved_problem.to_dict())


if __name__ == '__main__':
    KTG = KattisToGithub()
    KTG.get_run_details_from_sys_argv()
    KTG.create_folders_for_different_difficulties()
    KTG.load_solved_problem_status_csv()
    if KTG.login():
        if KTG.update:
            KTG.get_codes_for_solved_problems()
        else:
            KTG.get_solved_problems()
            KTG.get_codes_for_solved_problems()
        KTG.update_status_to_csv()
